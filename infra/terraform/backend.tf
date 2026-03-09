terraform {
  backend "s3" {
    bucket         = "traderx-terraform-state-599083837640"
    key            = "traderx/demo/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "traderx-terraform-lock"
    encrypt        = true
  }
}
