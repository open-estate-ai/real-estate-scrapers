data "aws_caller_identity" "current" {}


## Local variables
locals {
  resource_name_prefix_hyphenated = format("%s-%s", lower(var.env), lower(var.scraper_name))
  app_runner_service_name         = substr("${local.resource_name_prefix_hyphenated}-scraper-service", 0, 40)
}
