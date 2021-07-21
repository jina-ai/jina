module "jinad" {
  source            = "github.com/jina-ai/terraform-jina-jinad-aws"
  debug             = "true"
  branch            = var.branch
  port              = var.port
  scriptpath        = var.scriptpath
  instances         = local.dict
  availability_zone = "us-east-1a"
  additional_tags = merge(
    var.additional_tags,
    {
      "CI"     = "true",
      "branch" = var.branch
      "commit" = var.commit
    },
  )
}

locals {
  dict = { for i in range(1, var.instances + 1) : "CLOUDHOST${i}" => {
    type : "t2.medium"
    disk = {
      type = "gp2"
      size = 20
    }
    command : "sudo apt install -y jq"
  } }
}

variable "instances" {
  description = <<EOT
    Mention the number of instances to be created
    EOT
  type        = number
  default     = 1
}

variable "branch" {
  description = <<EOT
    Mention the branch of jina repo from which jinad will be built
    EOT
  type        = string
  default     = "master"
}

variable "port" {
  description = <<EOT
    Mention the jinad port to be mapped on host
    EOT
  type        = string
  default     = "8000"
}

variable "commit" {
  description = <<EOT
    Mention the commit hash (added to tags only)
    EOT
  type        = string
  default     = ""
}

variable "scriptpath" {
  description = <<EOT
    jinad setup script path (part of jina codebase)
    EOT
  type        = string
}

variable "additional_tags" {
  default     = {}
  description = <<EOT
    Additional resource tags
    EOT
  type        = map(string)
}

output "instance_ips" {
  description = <<EOT
    Elastic IPs of JinaD instances created as a map
    EOT
  value       = module.jinad.instance_ips
}
