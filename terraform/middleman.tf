# Buidspec for the middleman lmabda 
locals {
  buildspec_middleman = <<EOT
version: 0.2
phases:
  install:
    runtime-versions:
      python: 3.12
    commands:
      - echo "Installing dependencies..."
      - pip install --upgrade pip
      - pip install uv
  build:
    commands:
      - echo "Building middleman Lambda package..."
      - uv pip install -r middleman/pyproject.toml -t middleman/package/
      - cp middleman/get_presigned_url.py middleman/package/
      - cd middleman/package
      - zip -r ../../lambda_get_presigned_url.zip .
      - aws lambda update-function-code --function-name GetPresignedUrlLambda --zip-file fileb://../../lambda_get_presigned_url.zip
EOT
}

# Middleman Lambda
resource "aws_lambda_function" "get_presigned_url" {
  function_name    = "GetPresignedUrlLambda"
  handler          = "get_presigned_url.lambda_handler"
  runtime          = "python3.12"
  role             = aws_iam_role.lambda_exec.arn
  timeout          = 10
  memory_size      = 128
  filename         = "../middleman/lambda_get_presigned_url.zip"
  source_code_hash = filebase64sha256("../middleman/lambda_get_presigned_url.zip")
  environment {
    variables = {
      BUCKET_NAME = aws_s3_bucket.lambda_bucket.bucket
    }
  }
}

# API Gateway
resource "aws_api_gateway_rest_api" "middleman_api" {
  name        = "MiddlemanAPI"
  description = "API for generating pre-signed URLs"
}

resource "aws_api_gateway_resource" "presigned_url_resource" {
  rest_api_id = aws_api_gateway_rest_api.middleman_api.id
  parent_id   = aws_api_gateway_rest_api.middleman_api.root_resource_id
  path_part   = "get-presigned-url"
}

# POST Method
resource "aws_api_gateway_method" "presigned_url_method" {
  rest_api_id   = aws_api_gateway_rest_api.middleman_api.id
  resource_id   = aws_api_gateway_resource.presigned_url_resource.id
  http_method   = "POST"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "lambda_integration" {
  rest_api_id             = aws_api_gateway_rest_api.middleman_api.id
  resource_id             = aws_api_gateway_resource.presigned_url_resource.id
  http_method             = aws_api_gateway_method.presigned_url_method.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.get_presigned_url.invoke_arn
}

resource "aws_api_gateway_method_response" "post_response" {
  rest_api_id   = aws_api_gateway_rest_api.middleman_api.id
  resource_id   = aws_api_gateway_resource.presigned_url_resource.id
  http_method   = aws_api_gateway_method.presigned_url_method.http_method
  status_code   = "200"
  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = true
  }
}

resource "aws_api_gateway_integration_response" "post_integration_response" {
  rest_api_id   = aws_api_gateway_rest_api.middleman_api.id
  resource_id   = aws_api_gateway_resource.presigned_url_resource.id
  http_method   = aws_api_gateway_method.presigned_url_method.http_method
  status_code   = aws_api_gateway_method_response.post_response.status_code
  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = "'*'"
  }
  depends_on = [aws_api_gateway_integration.lambda_integration]
}

# OPTIONS Method (CORS Preflight)
resource "aws_api_gateway_method" "presigned_url_options" {
  rest_api_id   = aws_api_gateway_rest_api.middleman_api.id
  resource_id   = aws_api_gateway_resource.presigned_url_resource.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "options_integration" {
  rest_api_id             = aws_api_gateway_rest_api.middleman_api.id
  resource_id             = aws_api_gateway_resource.presigned_url_resource.id
  http_method             = aws_api_gateway_method.presigned_url_options.http_method
  type                    = "MOCK"
  request_templates = {
    "application/json" = "{\"statusCode\": 200}"
  }
}

resource "aws_api_gateway_method_response" "options_response" {
  rest_api_id   = aws_api_gateway_rest_api.middleman_api.id
  resource_id   = aws_api_gateway_resource.presigned_url_resource.id
  http_method   = aws_api_gateway_method.presigned_url_options.http_method
  status_code   = "200"
  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
    "method.response.header.Access-Control-Allow-Origin"  = true
  }
}

resource "aws_api_gateway_integration_response" "options_integration_response" {
  rest_api_id   = aws_api_gateway_rest_api.middleman_api.id
  resource_id   = aws_api_gateway_resource.presigned_url_resource.id
  http_method   = aws_api_gateway_method.presigned_url_options.http_method
  status_code   = aws_api_gateway_method_response.options_response.status_code
  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,X-Amz-Date,Authorization,X-Api-Key'"
    "method.response.header.Access-Control-Allow-Methods" = "'POST,OPTIONS'"
    "method.response.header.Access-Control-Allow-Origin"  = "'*'"
  }
}

# Deployment and Stage
resource "aws_api_gateway_deployment" "middleman_deployment" {
  depends_on = [
    aws_api_gateway_integration.lambda_integration,
    aws_api_gateway_integration.options_integration
  ]
  rest_api_id = aws_api_gateway_rest_api.middleman_api.id
}

resource "aws_api_gateway_stage" "prod_stage" {
  rest_api_id   = aws_api_gateway_rest_api.middleman_api.id
  deployment_id = aws_api_gateway_deployment.middleman_deployment.id
  stage_name    = "prod"
}

# Lambda Permission for API Gateway
resource "aws_lambda_permission" "api_gateway_invoke" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.get_presigned_url.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.middleman_api.execution_arn}/*/*"
}

# CodeBuild for Middleman
resource "aws_codebuild_project" "middleman_build" {
  name          = "middleman-build"
  service_role  = aws_iam_role.codebuild_role.arn
  build_timeout = "10"
  artifacts {
    type = "NO_ARTIFACTS"
  }
  environment {
    compute_type                = "BUILD_LAMBDA_1GB"
    image                       = "aws/codebuild/amazonlinux-x86_64-lambda-standard:python3.12"
    type                        = "LINUX_LAMBDA_CONTAINER"
    image_pull_credentials_type = "CODEBUILD"
  }
  source {
    type            = "GITHUB"
    location        = "https://github.com/${var.github_owner}/${var.github_repo}.git"
    git_clone_depth = 1
    buildspec       = local.buildspec_middleman
  }
}

# CodePipeline for Middleman
resource "aws_codepipeline" "middleman_pipeline" {
  name     = "middleman-pipeline"
  pipeline_type = "V2"
  role_arn = aws_iam_role.codepipeline_role.arn
  artifact_store {
    location = aws_s3_bucket.lambda_bucket.bucket
    type     = "S3"
  }
  stage {
    name = "Source"
    action {
      name             = "Source"
      category         = "Source"
      owner            = "AWS"
      provider         = "CodeStarSourceConnection"
      version          = "1"
      output_artifacts = ["source_output"]
      configuration = {
        ConnectionArn    = aws_codestarconnections_connection.github_connection.arn
        FullRepositoryId = "${var.github_owner}/${var.github_repo}"
        BranchName       = "main"
      }
    }
  }
  stage {
    name = "Build"
    action {
      name            = "Build"
      category        = "Build"
      owner           = "AWS"
      provider        = "CodeBuild"
      input_artifacts = ["source_output"]
      version         = "1"
      configuration = {
        ProjectName = aws_codebuild_project.middleman_build.name
      }
    }
  }
}

resource "aws_codepipeline_webhook" "middleman_webhook" {
  name            = "middleman-webhook"
  authentication  = "GITHUB_HMAC"
  target_action   = "Source"
  target_pipeline = aws_codepipeline.middleman_pipeline.name
  authentication_configuration {
    secret_token = var.github_webhook_secret
  }
  filter {
    json_path    = "$.ref"
    match_equals = "refs/heads/main"
  }
}
