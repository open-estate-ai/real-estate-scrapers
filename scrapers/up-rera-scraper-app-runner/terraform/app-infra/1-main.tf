module "app_runner" {
  source = "../tf-modules/app-runner"

  env          = var.env
  region       = var.resource_region
  scraper_name = var.scraper_name

  bedrock_llm_model          = var.bedrock_llm_model
  raw_s3_bucket_scraper_data = var.raw_s3_bucket_scraper_data
  raw_s3_prefix_scraper_data = var.raw_s3_prefix_scraper_data

  openai_api_key = var.openai_api_key
}
