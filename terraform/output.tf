output "lambda_function_arn" {
  value = aws_lambda_function.cv_parser.arn
}

output "codepipeline_name" {
  value = aws_codepipeline.cv_pipeline.name
}

output "s3_bucket_url" {
  value = "https://${aws_s3_bucket.lambda_bucket.bucket}.s3.amazonaws.com/"
}

