variable "scraper_tags" {
  description = "Scraper specific tags"
  type        = map(string)
  default     = {}
}

variable "scraper_name" {
  type = string
}

variable "bedrock_llm_model" {
  description = "Bedrock LLM model to use"
  type        = string
  default     = "bedrock/openai.gpt-oss-120b-1:0"
}
variable "raw_s3_bucket_scraper_data" {
  description = "S3 bucket to store raw scraper data"
  type        = string
}
variable "raw_s3_prefix_scraper_data" {
  description = "S3 prefix to store raw scraper data"
  type        = string
}

variable "openai_api_key" {
  description = "OpenAI API key for the scraper agent"
  type        = string
  sensitive   = true
}
