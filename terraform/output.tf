output "lambda_function_arn" {
  value = aws_lambda_function.cv_parser.arn
}

output "codepipeline_name" {
  value = aws_codepipeline.cv_pipeline.name
}

output "s3_bucket_url" {
  value = "https://${aws_s3_bucket.lambda_bucket.bucket}.s3.amazonaws.com/"
}

output "presigned_url_endpoint" {
  value       = "${aws_api_gateway_stage.prod_stage.invoke_url}/get-presigned-url"
  description = "The URL to call the GetPresignedUrlLambda via API Gateway"
}

