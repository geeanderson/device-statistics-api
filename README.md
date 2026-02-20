# Device Statistics API

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791?logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)
![Kubernetes](https://img.shields.io/badge/Kubernetes-EKS-326CE5?logo=kubernetes&logoColor=white)
![Terraform](https://img.shields.io/badge/Terraform-EKS-7B42BC?logo=terraform&logoColor=white)

---

## What is this?

Two backend APIs to handle device authentication events and track usage statistics per device type.

When a user authenticates from a device, that event gets logged. You can then query how many registrations happened per device type (iOS, Android, Watch, TV). Two services handle this — one public-facing, one internal — backed by a PostgreSQL database.

---

## Architecture

```
                       External Traffic
                              |
                              v
                   +---------------------+
                   |   Statistics API    |  ← public (port 8000)
                   |   POST /Log/auth    |
                   |   GET  /Log/auth/   |
                   |        statistics   |
                   +---------------------+
                              |
                   (internal network only)
                              |
                              v
                   +---------------------+
                   | Device Registration |  ← internal only
                   |       API           |
                   |  POST /Device/      |
                   |       register      |
                   +---------------------+
                              |
                              v
                   +---------------------+
                   |    PostgreSQL 16     |
                   +---------------------+
```

External clients only talk to the Statistics API. That service calls the Device Registration API internally. The registration service is never exposed outside.

---

## Tech Stack

| Technology     | Role                                        |
|----------------|---------------------------------------------|
| Python 3.11    | Application runtime                         |
| FastAPI        | Web framework for both APIs                 |
| psycopg2       | PostgreSQL driver (raw SQL, no ORM)         |
| httpx          | HTTP client for inter-service calls         |
| PostgreSQL 16  | Relational database                         |
| Docker Compose | Local development stack                     |
| Kubernetes     | Production deployment (EKS)                 |
| Terraform      | Infrastructure provisioning (EKS, VPC, IAM) |
| Karpenter      | Node autoscaling on EKS                     |
| AWS LBC        | ALB provisioning from Ingress objects       |

---

## Project Structure

```
device-statistics-api/
├── statistics-api/
│   ├── main.py
│   ├── requirements.txt
│   └── Dockerfile
├── device-registration-api/
│   ├── main.py
│   ├── requirements.txt
│   └── Dockerfile
├── k8s/                   # Kubernetes manifests
│   ├── kustomization.yaml
│   ├── namespace.yaml
│   ├── secrets.yaml
│   ├── configmap.yaml
│   ├── postgres/
│   ├── device-registration-api/
│   ├── statistics-api/
│   └── karpenter/
├── terraform/             # EKS cluster infrastructure
├── docker-compose.yml
└── README.md
```

---

## Running locally with Docker Compose

### Prerequisites

You only need **Docker Desktop** installed and running. No Python, no PostgreSQL, nothing else.

Check if Docker is ready:

```bash
docker --version
# Docker version 27.x.x or higher

docker compose version
# Docker Compose version v2.x.x or higher
```

If `docker compose version` fails, you may have the older `docker-compose` (v1) installed. Make sure Docker Desktop is up to date.

---

### Step 1 — Clone the repository

```bash
git clone https://github.com/geeanderson/device-statistics-api.git
cd device-statistics-api
```

---

### Step 2 — Set up environment variables

```bash
cp .env.example .env
```

The `.env.example` already has the correct values for running with Docker Compose. You can leave everything as is or change `DB_PASSWORD` to any value you want — just don't change `DB_HOST` or `DEVICE_API_URL`, those are service names that Docker uses internally.

---

### Step 3 — Start the stack

```bash
docker compose up --build
```

The first run downloads base images and installs dependencies — it takes about 2–3 minutes. After the first build, restarts are much faster.

Wait until you see this in the logs from both APIs:

```
statistics-api            | INFO:     Application startup complete.
device-registration-api   | INFO:     Application startup complete.
```

> You might see a database connection error in the first few seconds. That's normal — it means one of the APIs started before PostgreSQL finished initializing. Docker Compose retries automatically.

---

### Step 4 — Test the APIs

**Health check:**

```bash
curl http://localhost:8000/health
```

```json
{"status": "ok", "service": "statistics-api"}
```

**Log a device authentication event:**

```bash
curl -X POST http://localhost:8000/Log/auth \
  -H "Content-Type: application/json" \
  -d '{"userKey": "user-123", "deviceType": "iOS"}'
```

```json
{"statusCode": 200, "message": "Device registered successfully"}
```

Run a few more with different device types to have data to query:

```bash
curl -X POST http://localhost:8000/Log/auth \
  -H "Content-Type: application/json" \
  -d '{"userKey": "user-456", "deviceType": "Android"}'

curl -X POST http://localhost:8000/Log/auth \
  -H "Content-Type: application/json" \
  -d '{"userKey": "user-789", "deviceType": "iOS"}'
```

Valid device types: `iOS`, `Android`, `Watch`, `TV`. Anything else returns 400.

**Query statistics:**

```bash
curl "http://localhost:8000/Log/auth/statistics?deviceType=iOS"
```

```json
{"deviceType": "iOS", "count": 2}
```

If you prefer a browser over curl, FastAPI provides interactive docs at:
- http://localhost:8000/docs

---

### Step 5 — Stop the environment

```bash
# Stop containers but keep database data
docker compose down

# Stop and delete database data (clean slate for next run)
docker compose down -v
```

---

## Running on Kubernetes (EKS + Terraform)

This section walks through provisioning the EKS cluster from scratch and deploying both APIs.

### Prerequisites

You need the following tools installed before starting:

**Terraform >= 1.9.0**

```bash
terraform version
# Terraform v1.9.x or higher
```

If not installed: https://developer.hashicorp.com/terraform/install

---

**AWS CLI (any recent version)**

```bash
aws --version
# aws-cli/2.x.x
```

If not installed: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html

---

**kubectl**

```bash
kubectl version --client
# Client Version: v1.x.x
```

If not installed: https://kubernetes.io/docs/tasks/tools/

---

**AWS credentials configured**

```bash
aws sts get-caller-identity
```

This should return your account ID, user/role ARN, and user ID. If you get an error, run `aws configure` first and provide your access key, secret key, and default region (`us-east-1`).

The IAM identity must have permissions to create: EKS clusters, VPCs, IAM roles, EC2 instances, SQS queues, and Helm releases. Admin access works. For scoped permissions, see the AWS EKS documentation.

---

### Step 1 — Configure Terraform variables

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars
```

The defaults in `terraform.tfvars.example` are ready to use. Open `terraform.tfvars` and adjust the `region` if you want to deploy somewhere other than `us-east-1`.

---

### Step 2 — Initialize Terraform

```bash
terraform init
```

This downloads the AWS, Helm, and Local providers, and the EKS module. Takes about 1–2 minutes.

Expected output:

```
Terraform has been successfully initialized!
```

---

### Step 3 — Review what will be created

```bash
terraform plan
```

Review the output before applying. You should see around 90+ resources to be created, including the VPC, EKS cluster, IAM roles, SQS queue, and Helm releases for Karpenter and the AWS Load Balancer Controller.

---

### Step 4 — Provision the cluster

```bash
terraform apply
```

Type `yes` when prompted. This takes **15–20 minutes** — EKS cluster creation is the slowest part.

When it finishes, you'll see:

```
Apply complete! Resources: 92 added, 0 changed, 0 destroyed.

Outputs:

cluster_endpoint  = "https://xxxx.gr7.us-east-1.eks.amazonaws.com"
cluster_name      = "device-statistics"
cluster_version   = "1.35"
configure_kubectl = "aws eks update-kubeconfig --region us-east-1 --name device-statistics"
private_subnets   = [...]
public_subnets    = [...]
vpc_id            = "vpc-xxxx"
```

---

### Step 5 — Configure kubectl

Copy the `configure_kubectl` command from the Terraform output and run it:

```bash
aws eks update-kubeconfig --region us-east-1 --name device-statistics
```

```
Added new context arn:aws:eks:us-east-1:xxxx:cluster/device-statistics to ~/.kube/config
```

Verify the nodes are ready:

```bash
kubectl get nodes
```

```
NAME                          STATUS   ROLES    AGE   VERSION
ip-10-0-x-x.ec2.internal      Ready    <none>   5m    v1.35.x-eks-xxxxx
ip-10-0-x-x.ec2.internal      Ready    <none>   5m    v1.35.x-eks-xxxxx
```

You should see 2 nodes (system node group). If they show `NotReady`, wait another minute and try again.

---

### Step 6 — Apply Karpenter manifests

The EC2NodeClass file is generated by Terraform during `apply` (it fills in the cluster name and IAM role). Apply both manifests:

```bash
cd ..
kubectl apply -f k8s/karpenter/ec2nodeclass.yaml
kubectl apply -f k8s/karpenter/nodepool.yaml
```

```
ec2nodeclass.karpenter.k8s.aws/default created
nodepool.karpenter.sh/default created
```

Confirm Karpenter is running:

```bash
kubectl get pods -n karpenter
```

```
NAME                         READY   STATUS    RESTARTS   AGE
karpenter-xxxx-xxxx          1/1     Running   0          10m
karpenter-xxxx-xxxx          1/1     Running   0          10m
```

---

### Step 7 — Deploy the application

The manifests use Kustomize to make it easy to override the Docker image registry. Kustomize is built into `kubectl` — no extra tools needed.

**If you built and pushed your own images**, edit `k8s/kustomization.yaml` and change the registry:

```yaml
images:
  - name: geeanderson/statistics-api
    newName: yourusername/statistics-api  # ← change this
    newTag: latest
  - name: geeanderson/device-registration-api
    newName: yourusername/device-registration-api  # ← change this
    newTag: latest
```

**If you're using the public images from DockerHub**, no changes needed — skip to the apply step.

Apply all manifests at once:

```bash
kubectl apply -k k8s/
```

This creates the namespace, secrets, configmap, postgres, and both APIs in the correct order.

Wait for all pods to reach `Running` state:

```bash
kubectl get pods -n device-statistics
```

```
NAME                                      READY   STATUS    RESTARTS   AGE
device-registration-api-xxxx-xxxx         1/1     Running   0          2m
device-registration-api-xxxx-xxxx         1/1     Running   0          2m
postgres-xxxx-xxxx                        1/1     Running   0          3m
statistics-api-xxxx-xxxx                  1/1     Running   0          2m
statistics-api-xxxx-xxxx                  1/1     Running   0          2m
```

> If a pod shows `Pending`, Karpenter is likely provisioning a new node. This takes about 30–60 seconds on the first deployment. Run `kubectl get nodes` to see the new node appear.

---

### Step 8 — Get the ALB address

```bash
kubectl get ingress -n device-statistics
```

```
NAME             CLASS   HOSTS   ADDRESS                                                                  PORTS   AGE
statistics-api   alb     *       k8s-devicest-statisti-xxxx.us-east-1.elb.amazonaws.com                  80      2m
```

The ADDRESS column may take 1–2 minutes to appear while AWS provisions the ALB. If it's empty, wait and run the command again.

Set the address as a variable for the tests:

```bash
ALB="k8s-devicest-statisti-xxxx.us-east-1.elb.amazonaws.com"
```

Replace the value with the actual ADDRESS from the command output.

---

### Step 9 — Test the APIs

**Health check:**

```bash
curl http://$ALB/health
```

```json
{"status": "ok", "service": "statistics-api"}
```

**Log a device authentication event:**

```bash
curl -X POST http://$ALB/Log/auth \
  -H "Content-Type: application/json" \
  -d '{"userKey": "user-123", "deviceType": "iOS"}'
```

```json
{"statusCode": 200, "message": "Device registered successfully"}
```

**Log a few more events:**

```bash
curl -X POST http://$ALB/Log/auth \
  -H "Content-Type: application/json" \
  -d '{"userKey": "user-456", "deviceType": "Android"}'

curl -X POST http://$ALB/Log/auth \
  -H "Content-Type: application/json" \
  -d '{"userKey": "user-789", "deviceType": "iOS"}'
```

**Test validation (invalid device type):**

```bash
curl -X POST http://$ALB/Log/auth \
  -H "Content-Type: application/json" \
  -d '{"userKey": "user-000", "deviceType": "Windows"}'
```

```json
{"detail": "Invalid deviceType 'Windows'. Allowed values: ['Android', 'TV', 'Watch', 'iOS']"}
```

**Query statistics:**

```bash
curl "http://$ALB/Log/auth/statistics?deviceType=iOS"
```

```json
{"deviceType": "iOS", "count": 2}
```

```bash
curl "http://$ALB/Log/auth/statistics?deviceType=Android"
```

```json
{"deviceType": "Android", "count": 1}
```

---

### Step 10 — Tear down (optional)

To destroy the cluster and all AWS resources:

> Make sure the Kubernetes resources (namespace, deployments, ingress) are deleted before running `terraform destroy`. The ALB created by the Ingress object must be removed first, otherwise Terraform will fail trying to delete the VPC while a load balancer still exists in it.
>
> ```bash
> kubectl delete -k k8s/
> ```
>
> Wait until all resources are fully deleted (check with `kubectl get all -n device-statistics`), then run `terraform destroy`.

```bash
cd terraform
terraform destroy
```

Type `yes` when prompted. This removes everything created by Terraform — VPC, EKS cluster, IAM roles, load balancer, and all associated resources. Takes about 10–15 minutes.

---

## API Reference

### Statistics API — port 8000

| Method | Path                   | Description                           |
|--------|------------------------|---------------------------------------|
| GET    | /health                | Health check                          |
| POST   | /Log/auth              | Log a device authentication event     |
| GET    | /Log/auth/statistics   | Get registration count by device type |

**POST /Log/auth** — request body:

```json
{
  "userKey": "string",
  "deviceType": "iOS | Android | Watch | TV"
}
```

**GET /Log/auth/statistics** — query param: `?deviceType=iOS`

### Device Registration API — port 8001 (internal only)

| Method | Path               | Description                          |
|--------|--------------------|--------------------------------------|
| GET    | /health            | Health check                         |
| POST   | /Device/register   | Save a device registration to the DB |

This API is not reachable from outside. In Docker Compose it runs on an internal network with no port exposed to the host. In Kubernetes it is a ClusterIP service with no Ingress.

---

## Security

- No credentials in code — everything goes through environment variables and Kubernetes Secrets
- SQL queries use parameterized statements (no SQL injection risk)
- The Device Registration API is not reachable from outside the cluster
- Containers run as non-root users
- Kubernetes NetworkPolicies restrict traffic between pods
- Resource limits set on all deployments

---

## License

MIT
