terraform {
  required_version = ">= 1.6.0"
  required_providers {
    null = { source = "hashicorp/null" }
  }
}

provider "null" {}

# Local cluster via k3d (shell exec for demo)
resource "null_resource" "k3d_cluster" {
  provisioner "local-exec" {
    command = "bash scripts/k3d-setup.sh"
  }
}
