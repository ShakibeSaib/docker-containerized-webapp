# Docker Containerized Web Application

## Project Overview

This project demonstrates how to containerize and deploy a simple Python web application using Docker on an AWS EC2 Ubuntu Linux server.

The project starts with a fresh Ubuntu EC2 instance and progresses through Docker installation, application development, image creation, container deployment, networking, health checks, and basic container operations.

The project is intentionally simple at the application layer so the focus remains on **DevOps practices and infrastructure**.

---

## What This Project Demonstrates

* AWS EC2
* Ubuntu Linux
* SSH access
* Docker Engine
* Docker images
* Docker containers
* Dockerfile
* Docker port mapping
* Docker environment variables
* Docker restart policies
* Docker health checks
* Gunicorn
* AWS Security Groups
* Container troubleshooting
* Basic container lifecycle management

---

# 1. Architecture

The final deployment looks like this:

```text
                         Internet
                            |
                            |
                     Windows Browser
                            |
                            | HTTP :8080
                            |
                            v
                  +--------------------+
                  | AWS Security Group |
                  |                    |
                  | TCP 8080           |
                  +---------+----------+
                            |
                            v
                  +--------------------+
                  | AWS EC2            |
                  | Ubuntu Linux       |
                  |                    |
                  | Host :8080         |
                  |       |            |
                  |       v            |
                  | Docker             |
                  |       |            |
                  |       v            |
                  | Container :8080    |
                  |       |            |
                  |       v            |
                  | Gunicorn           |
                  |       |            |
                  |       v            |
                  | Flask Application  |
                  +--------------------+
```

The application request flows through several layers:

```text
Browser
   ↓
Internet
   ↓
AWS Security Group
   ↓
EC2
   ↓
Docker port mapping
   ↓
Container
   ↓
Gunicorn
   ↓
Flask
   ↓
HTTP Response
```

---

# 2. AWS EC2 Environment

The application is hosted on an Ubuntu Linux EC2 instance.

Example environment:

| Component        | Configuration     |
| ---------------- | ----------------- |
| Cloud Provider   | AWS               |
| Service          | EC2               |
| Operating System | Ubuntu Server LTS |
| Instance Type    | t3.large          |
| Architecture     | x86_64            |
| Root Storage     | EBS gp3           |
| SSH              | Port 22           |
| Application      | Port 8080         |

> EC2 instance specifications and pricing can change. Verify current AWS pricing and eligibility before creating resources.

---

# 3. Connect to the EC2 Instance

From Windows PowerShell:

```powershell
ssh -i ".\Shakibe_SSH.pem" devops@<EC2_PUBLIC_IP>
```

Verify the current user:

```bash
whoami
```

Expected:

```text
devops
```

---

# 4. Install Docker

## What are we doing?

We are installing Docker Engine on the Ubuntu EC2 server.

## Why are we doing it?

Docker allows us to package an application and its dependencies into a portable container.

Instead of installing the application runtime directly on the EC2 host, we will run the application inside a container.

The architecture becomes:

```text
EC2
 |
 +-- Ubuntu
 |
 +-- Docker
      |
      +-- Application Container
```

## Remove conflicting packages

```bash
sudo apt remove -y docker.io docker-doc docker-compose docker-compose-v2 podman-docker containerd runc
```

Packages that are not installed can safely be ignored.

---

## Install prerequisites

```bash
sudo apt update
```

```bash
sudo apt install -y ca-certificates curl
```

---

## Add Docker's repository signing key

```bash
sudo install -m 0755 -d /etc/apt/keyrings
```

```bash
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
  -o /etc/apt/keyrings/docker.asc
```

```bash
sudo chmod a+r /etc/apt/keyrings/docker.asc
```

---

## Add Docker's official repository

```bash
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
```

Update package information:

```bash
sudo apt update
```

---

## Install Docker

```bash
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

---

# 5. Verify Docker Installation

## What are we doing?

We are verifying that Docker Engine was installed correctly and that the Docker daemon can run containers.

## Why are we doing it?

Installing a package does not necessarily mean the complete Docker environment is working.

We want to verify:

1. Docker CLI works.
2. Docker daemon works.
3. Docker can communicate with Docker Hub.
4. Docker can pull an image.
5. Docker can create a container.
6. Docker can execute the container.

## Verify the Docker service

```bash
sudo systemctl status docker
```

Expected:

```text
Active: active (running)
```

Exit the status screen with:

```text
q
```

Check the version:

```bash
docker --version
```

---

# 6. Run Docker Hello World

## What are we doing?

We are running Docker's official test container.

```bash
docker run hello-world
```

## Why are we doing it?

This verifies the complete Docker workflow.

Docker performs:

```text
Docker CLI
    ↓
Docker daemon
    ↓
Docker Hub
    ↓
Pull image
    ↓
Create container
    ↓
Execute container
    ↓
Return output
```

## How do we verify it worked?

Successful output contains:

```text
Hello from Docker!
This message shows that your installation appears to be working correctly.
```

This confirms Docker is functional.

---

# 7. Allow the DevOps User to Use Docker

## What are we doing?

We are adding the `devops` Linux user to the Docker group.

```bash
sudo usermod -aG docker $USER
```

## Why are we doing it?

Without this configuration, Docker commands may require:

```bash
sudo docker ...
```

We want the dedicated `devops` user to manage Docker directly.

After adding the group, log out:

```bash
exit
```

Reconnect:

```powershell
ssh -i ".\Shakibe_SSH.pem" devops@<EC2_PUBLIC_IP>
```

Verify:

```bash
groups
```

The output should contain:

```text
docker
```

Then:

```bash
docker ps
```

The command should work without `sudo`.

### Security consideration

Membership in the Docker group effectively provides root-level control over the host.

This is acceptable for our dedicated DevOps lab, but it is an important security consideration in production environments.

---

# 8. Understand Docker Images and Containers

Run:

```bash
docker images
```

We should see:

```text
hello-world
```

Now:

```bash
docker ps
```

The container may not appear.

Why?

Because `docker ps` shows **running containers**.

Run:

```bash
docker ps -a
```

Now the completed `hello-world` container appears.

The distinction is:

```text
docker images
        ↓
Docker image inventory

docker ps
        ↓
Running containers

docker ps -a
        ↓
All containers
```

### Important concept

An **image** is a template.

A **container** is a running or stopped instance created from that image.

```text
Docker Image
     |
     +------> Container
     |
     +------> Container
     |
     +------> Container
```

---

# 9. Create the Application

## What are we doing?

We are creating a small Python Flask web application.

Project directory:

```text
devops-containerized-webapp/
├── app/
│   ├── app.py
│   └── requirements.txt
└── Dockerfile
```

## Why are we doing it?

We want a simple application that allows us to focus on Docker and deployment concepts rather than application complexity.

Create the project:

```bash
mkdir -p ~/devops-containerized-webapp/app
```

Move into it:

```bash
cd ~/devops-containerized-webapp
```

---

# 10. Create the Flask Application

Create:

```bash
nano app/app.py
```

Application:

```python
from flask import Flask
import os
import socket

app = Flask(__name__)


@app.route("/")
def home():
    hostname = socket.gethostname()
    environment = os.getenv("APP_ENV", "development")

    return f"""
    <html>
        <head>
            <title>DevOps Containerized Web App</title>
        </head>
        <body>
            <h1>DevOps Containerized Web Application</h1>
            <p>Application is running inside Docker.</p>
            <p>Environment: {environment}</p>
            <p>Container hostname: {hostname}</p>
        </body>
    </html>
    """


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
```

---

# 11. Create Python Dependencies

Create:

```bash
nano app/requirements.txt
```

Add:

```text
Flask==3.1.2
gunicorn==23.0.0
```

---

# 12. Create the Dockerfile

## What are we doing?

We are defining how Docker should build the application image.

## Why are we doing it?

A Dockerfile provides a repeatable process for building the application environment.

Instead of manually installing:

```text
Python
Flask
Gunicorn
Application files
```

we define everything as code.

This gives us a reproducible build.

Create:

```bash
nano Dockerfile
```

Add:

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY app/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY app/ .

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080', timeout=3)" || exit 1

CMD ["gunicorn", "--bind", "0.0.0.0:8080", "app:app"]
```

---

# 13. Dockerfile Explanation

### `FROM`

```dockerfile
FROM python:3.12-slim
```

Provides a lightweight Python base image.

---

### `WORKDIR`

```dockerfile
WORKDIR /app
```

Sets the working directory inside the container.

---

### `COPY`

```dockerfile
COPY app/requirements.txt .
```

Copies the dependency file into the image.

---

### `RUN`

```dockerfile
RUN pip install --no-cache-dir -r requirements.txt
```

Installs the Python dependencies.

---

### Second `COPY`

```dockerfile
COPY app/ .
```

Copies the application code into the image.

---

### `EXPOSE`

```dockerfile
EXPOSE 8080
```

Documents that the application listens on port 8080.

`EXPOSE` by itself does **not** make the port publicly accessible.

---

### `HEALTHCHECK`

```dockerfile
HEALTHCHECK ...
```

Allows Docker to determine whether the application is actually responding.

---

### `CMD`

```dockerfile
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "app:app"]
```

Starts the application using Gunicorn.

---

# 14. Why Gunicorn?

Initially, the application used:

```text
python app.py
```

Flask warned:

```text
WARNING: This is a development server.
```

For a production-style deployment, we replaced the development server with Gunicorn.

The architecture is now:

```text
Docker
  |
  v
Gunicorn
  |
  v
Flask
  |
  v
Application
```

This is more appropriate for a deployment-oriented project.

---

# 15. Build the Docker Image

## What are we doing?

We are building a Docker image from our Dockerfile and application source.

```bash
docker build -t devops-webapp:1.2 .
```

## Why are we doing it?

The image packages:

```text
Python
Flask
Gunicorn
Application code
Dependencies
Startup configuration
```

into a reproducible artifact.

## How do we verify it worked?

```bash
docker images
```

Expected:

```text
devops-webapp   1.2
```

---

# 16. Run the Container

## What are we doing?

We are creating and starting a container from the Docker image.

```bash
docker run -d \
  --name devops-webapp \
  -p 8080:8080 \
  -e APP_ENV=production \
  --restart unless-stopped \
  devops-webapp:1.2
```

## Why are we doing it?

The Docker image is a static artifact.

The container is the actual running application.

---

## Command breakdown

### Detached mode

```text
-d
```

Runs the container in the background.

### Container name

```text
--name devops-webapp
```

Gives the container a predictable name.

### Port mapping

```text
-p 8080:8080
```

Maps:

```text
EC2 host port 8080
        ↓
Container port 8080
```

### Environment variable

```text
-e APP_ENV=production
```

Creates:

```text
APP_ENV=production
```

inside the container.

### Restart policy

```text
--restart unless-stopped
```

Allows Docker to restart the container after Docker/host restarts unless the container was intentionally stopped.

---

# 17. Verify the Container

Run:

```bash
docker ps
```

Expected:

```text
devops-webapp
Up
0.0.0.0:8080->8080/tcp
```

---

# 18. Check Container Logs

```bash
docker logs devops-webapp
```

We should see Gunicorn starting.

We should no longer see the Flask development-server warning.

---

# 19. Test the Application Locally

## What are we doing?

We are testing the application directly from the EC2 server.

```bash
curl http://localhost:8080
```

## Why are we doing it?

This isolates the application/container from external networking.

We are testing:

```text
Application
   ↓
Container
   ↓
EC2 localhost
```

before troubleshooting AWS networking.

## How do we verify it worked?

The command should return the application's HTML.

For example:

```text
DevOps Containerized Web Application

Application is running inside Docker.

Environment: production
```

The response also displays the container hostname.

---

# 20. Docker Port Mapping

Our application listens inside the container on:

```text
8080
```

Docker maps it to the EC2 host:

```text
8080
```

Therefore:

```text
EC2 :8080
    ↓
Docker
    ↓
Container :8080
```

We can verify this with:

```bash
docker port devops-webapp
```

Expected:

```text
8080/tcp -> 0.0.0.0:8080
```

---

# 21. Configure AWS Security Group

## What are we doing?

We are allowing inbound TCP traffic on port 8080 through the EC2 Security Group.

## Why are we doing it?

AWS Security Groups act as a virtual firewall.

Even if Docker exposes:

```text
0.0.0.0:8080
```

AWS can still block the incoming traffic.

Add an inbound rule:

```text
Type: Custom TCP
Port: 8080
Source: My IP
```

For a lab environment, restricting the source to your own IP is preferable to:

```text
0.0.0.0/0
```

---

# 22. Access the Application from the Internet

Open:

```text
http://<EC2_PUBLIC_IP>:8080
```

Example:

```text
http://13.223.44.81:8080
```

The application should display:

```text
DevOps Containerized Web Application

Application is running inside Docker.

Environment: production

Container hostname: <container-id>
```

---

# 23. Network Troubleshooting Approach

If the browser cannot access the application, don't immediately change everything.

Troubleshoot layer by layer.

```text
Browser
   ↓
AWS Security Group
   ↓
EC2
   ↓
Docker Port Mapping
   ↓
Container
   ↓
Application
```

Start at the application:

```bash
curl http://localhost:8080
```

If that works, check the container:

```bash
docker ps
```

Check port mapping:

```bash
docker port devops-webapp
```

Check logs:

```bash
docker logs devops-webapp
```

Then check AWS Security Group.

This approach prevents random troubleshooting.

---

# 24. Docker Health Check

## What are we doing?

We added:

```dockerfile
HEALTHCHECK
```

to the Dockerfile.

## Why are we doing it?

A running process does not necessarily mean the application is healthy.

For example:

```text
Container = Running
Application = Not responding
```

A health check provides an additional signal.

## How do we verify it?

```bash
docker ps
```

Eventually the status should show:

```text
(healthy)
```

Or directly:

```bash
docker inspect --format='{{.State.Health.Status}}' devops-webapp
```

Expected:

```text
healthy
```

---

# 25. Inspect Container Resources

## Container processes

```bash
docker top devops-webapp
```

## Resource usage

```bash
docker stats devops-webapp
```

This shows:

* CPU
* Memory
* Network
* Block I/O

Exit with:

```text
Ctrl+C
```

---

# 26. Container Logs

View the last 50 lines:

```bash
docker logs --tail 50 devops-webapp
```

Follow logs in real time:

```bash
docker logs -f devops-webapp
```

Exit with:

```text
Ctrl+C
```

---

# 27. Container Lifecycle

Docker containers have a lifecycle.

```text
             docker run
                 |
                 v
              Created
                 |
                 v
              Running
                 |
          +------+------+
          |             |
     docker stop    docker restart
          |             |
          v             |
        Stopped <-------+
```

Stop:

```bash
docker stop devops-webapp
```

Check:

```bash
docker ps
```

Start again:

```bash
docker start devops-webapp
```

Check:

```bash
docker ps
```

---

# 28. Project Files

The final project structure is:

```text
devops-containerized-webapp/
├── .dockerignore
├── Dockerfile
└── app/
    ├── app.py
    └── requirements.txt
```

---

# 29. `.dockerignore`

The `.dockerignore` file prevents unnecessary files from being sent into the Docker build context.

Example:

```text
.git
.gitignore
README.md
.env
.venv
__pycache__
*.pyc
*.pyo
*.pyd
.pytest_cache
```

This helps:

* Reduce build context
* Reduce image build overhead
* Prevent accidental inclusion of local files
* Reduce the chance of including secrets

---

# 30. Useful Docker Commands

| Command            | Purpose                              |
| ------------------ | ------------------------------------ |
| `docker --version` | Show Docker version                  |
| `docker images`    | List images                          |
| `docker ps`        | List running containers              |
| `docker ps -a`     | List all containers                  |
| `docker build`     | Build an image                       |
| `docker run`       | Create and start a container         |
| `docker stop`      | Stop a container                     |
| `docker start`     | Start a stopped container            |
| `docker restart`   | Restart a container                  |
| `docker rm`        | Remove a container                   |
| `docker rmi`       | Remove an image                      |
| `docker logs`      | View container logs                  |
| `docker stats`     | View resource usage                  |
| `docker top`       | View container processes             |
| `docker inspect`   | Inspect Docker objects               |
| `docker port`      | Show port mappings                   |
| `docker exec`      | Execute a command inside a container |

---

# 31. Troubleshooting Checklist

## Container isn't running

```bash
docker ps
docker ps -a
```

Then:

```bash
docker logs devops-webapp
```

---

## Application isn't responding

Test from EC2:

```bash
curl http://localhost:8080
```

If it fails:

```bash
docker logs devops-webapp
```

Check:

```bash
docker ps
```

---

## Port isn't accessible externally

Check Docker:

```bash
docker port devops-webapp
```

Check EC2:

```bash
sudo ss -tulpn | grep 8080
```

Check AWS Security Group:

```text
TCP 8080
Source: My IP
```

---

## Container is unhealthy

Check:

```bash
docker inspect --format='{{.State.Health.Status}}' devops-webapp
```

Then:

```bash
docker logs devops-webapp
```

---

# 32. What We Learned

This project introduced several fundamental DevOps concepts.

### Containers

Containers provide an isolated runtime for applications.

### Images

Images are immutable artifacts used to create containers.

### Dockerfiles

Dockerfiles define how application images are built.

### Port Mapping

Docker maps host ports to container ports.

```text
Host :8080
   ↓
Container :8080
```

### Environment Variables

Application configuration can be provided externally:

```text
APP_ENV=production
```

### Health Checks

A running container is not necessarily a healthy application.

### Restart Policies

Containers can automatically restart after infrastructure events.

### Layered Networking

AWS networking and Docker networking are separate layers.

### Troubleshooting

Troubleshooting should proceed from the application outward rather than randomly changing configuration.

---
