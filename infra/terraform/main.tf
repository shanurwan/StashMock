terraform {
  required_version = ">= 1.6"
}

provider "null" {}

resource "null_resource" "cluster" {
  provisioner "local-exec" {
    command = "bash ../../scripts/cluster-up.sh ${var.cluster_name} ${var.registry_port}"
  }

  triggers = {
    cluster_name  = var.cluster_name
    registry_port = var.registry_port
  }
}

variable "cluster_name" {
  type    = string
  default = "stashmock"
}

variable "registry_port" {
  type    = number
  default = 5001
}
