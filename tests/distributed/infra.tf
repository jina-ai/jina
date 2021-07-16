module "jinad" {
  source       = "jina-ai/jinad-aws/jina"
  debug        = "true"
  branch       = var.branch
  port         = var.port
  scriptpath   = "scripts/setup-jinad.sh"
  instances = {
    CLOUDHOST1 : {
      type : "t2.micro"
      disk = {
        type = "gp2"
        size = 20
      }
      command : "sudo apt install -y jq"
    }
    CLOUDHOST2 : {
      type : "t2.micro"
      disk = {
        type = "gp2"
        size = 20
      }
      command : "sudo apt install -y jq"
    }
  }
  availability_zone = "us-east-1a"
  additional_tags = {
    "CI" = "true"
  }
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

