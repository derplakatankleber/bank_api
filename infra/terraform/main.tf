terraform {
  required_version = ">= 1.5.0"
  required_providers {
    docker = {
      source  = "kreuzwerker/docker"
      version = "~> 3.0"
    }
  }
}

provider "docker" {}

variable "image_tag" {
  description = "Tag to give the locally built bank-api image"
  type        = string
  default     = "bank-api:tf"
}

variable "api_port" {
  description = "External port to expose the API on"
  type        = number
  default     = 8000
}

variable "comdirect_token" {
  description = "Access token for the comdirect sandbox"
  type        = string
  sensitive   = true
}

variable "comdirect_user" {
  description = "Sandbox user identifier"
  type        = string
}

variable "secret_key" {
  description = "Secret key for signing tokens"
  type        = string
  sensitive   = true
}

resource "docker_network" "bank_api" {
  name = "bank-api"
}

resource "docker_volume" "postgres" {
  name = "bank-api-postgres"
}

resource "docker_image" "bank_api" {
  name = var.image_tag
  build {
    context    = "${path.module}/../.."
    dockerfile = "${path.module}/../../Dockerfile"
  }
}

resource "docker_container" "db" {
  name  = "bank-api-db"
  image = "postgres:16-alpine"

  restart    = "unless-stopped"
  networks_advanced {
    name = docker_network.bank_api.name
  }

  env = [
    "POSTGRES_DB=bankapi",
    "POSTGRES_USER=bankapi",
    "POSTGRES_PASSWORD=${var.secret_key}",
  ]

  mounts {
    target = "/var/lib/postgresql/data"
    source = docker_volume.postgres.name
    type   = "volume"
  }

  healthcheck {
    test     = ["CMD-SHELL", "pg_isready -U bankapi"]
    interval = "10s"
    timeout  = "5s"
    retries  = 5
  }
}

resource "docker_container" "api" {
  name  = "bank-api"
  image = docker_image.bank_api.image_id

  restart    = "unless-stopped"
  networks_advanced {
    name = docker_network.bank_api.name
  }

  env = [
    "COMDIRECT_SANDBOX_TOKEN=${var.comdirect_token}",
    "COMDIRECT_SANDBOX_USER=${var.comdirect_user}",
    "BANK_API_SECRET_KEY=${var.secret_key}",
    "BANK_API_DATABASE_URL=postgresql+psycopg2://bankapi:${var.secret_key}@${docker_container.db.name}:5432/bankapi",
  ]

  ports {
    internal = 8000
    external = var.api_port
  }

  depends_on = [docker_container.db]
}
