# Remote state backend (TARGET_ARCHITECTURE_CONSTRAINTS.md §6: "State stored in a
# remote backend (S3/Azure Blob) with state locking").
#
# NOTE: the literal token ACCOUNT_ID below is intentional. Terraform backend blocks
# cannot use variables or interpolation, so the real 12-digit AWS account id is
# substituted at init time by the parent/bootstrap process, e.g.:
#
#   sed -i "s/ACCOUNT_ID/$(aws sts get-caller-identity --query Account --output text)/" backend.tf
#   terraform init
#
# The state bucket (traderx-tfstate-<account id>) and the lock table
# (traderx-tfstate-lock) are created out-of-band by the bootstrap process before
# the first init; they are deliberately NOT managed by this configuration to avoid
# a chicken-and-egg dependency between the state store and the state.
terraform {
  backend "s3" {
    bucket         = "traderx-tfstate-ACCOUNT_ID"
    key            = "traderx/acme_corp/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "traderx-tfstate-lock"
    encrypt        = true
  }
}
