# Buidspec for the backend CVParserLambda
locals {
  buildspec_lambda = <<EOT
version: 0.2
phases:
  install:
    runtime-versions:
      python: 3.12

  pre_build:
    commands:
      - echo "Navigating to backend folder"
      - cd backend
      - echo "Creating package directory"
      - mkdir -p package
      - echo "Decrypting credentials..."
      - aws kms decrypt \
          --ciphertext-blob fileb://google-credentials.json.encrypted \
          --output text \
          --query Plaintext | base64 --decode > ./package/google-credentials.json

  build:
    commands:
      - echo "Building backend package"
      - pip install --target=package -r requirements.txt
      - cp -r lambda_function.py models/ utils/ package/
      - cd package
      - zip -r ../lambda_function.zip .
      - cd ..
      - echo "Deploying to AWS Lambda"
      - aws lambda update-function-code --function-name CVParserLambda --zip-file fileb://lambda_function.zip

EOT
}

# Lambda Role and Function
resource "aws_iam_role" "lambda_exec" {
  name = "cv-parser-lambda-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy" "lambda_policy" {
  name = "cv-parser-lambda-policy"
  role = aws_iam_role.lambda_exec.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject"
        ]
        Resource = "${aws_s3_bucket.lambda_bucket.arn}/*"
      },
      {
        Effect   = "Allow"
        Action   = "ses:SendEmail"
        Resource = "*"
      }
    ]
  })
}

resource "aws_lambda_function" "cv_parser" {
  function_name    = "CVParserLambda"
  handler          = "lambda_function.lambda_handler"
  runtime          = "python3.12"
  role             = aws_iam_role.lambda_exec.arn
  timeout          = 30
  memory_size      = 256
  filename         = "../backend/lambda_function.zip"
  source_code_hash = filebase64sha256("../backend/lambda_function.zip")
}

# S3 Trigger
resource "aws_s3_bucket_notification" "lambda_trigger" {
  bucket = aws_s3_bucket.lambda_bucket.id
  lambda_function {
    lambda_function_arn = aws_lambda_function.cv_parser.arn
    events              = ["s3:ObjectCreated:*"]
    filter_suffix       = ".pdf"
  }
  depends_on = [aws_lambda_permission.s3_trigger]
}

resource "aws_lambda_permission" "s3_trigger" {
  statement_id  = "AllowS3Invoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.cv_parser.function_name
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.lambda_bucket.arn
}

# CodeBuild for CVParserLambda
resource "aws_codebuild_project" "backend_build" {
  name          = "cv-parser-backend-build"
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
    buildspec       = local.buildspec_lambda
  }
}

# CodePipeline for CVParserLambda
resource "aws_codepipeline" "cv_pipeline" {
  name     = "cv-parser-pipeline"
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
        ProjectName = aws_codebuild_project.backend_build.name
      }
    }
  }
}

resource "aws_codepipeline_webhook" "github_webhook" {
  name            = "cv-parser-webhook"
  authentication  = "GITHUB_HMAC"
  target_action   = "Source"
  target_pipeline = aws_codepipeline.cv_pipeline.name

  authentication_configuration {
    secret_token = var.github_webhook_secret
  }

  filter {
    json_path    = "$.ref"
    match_equals = "refs/heads/main"
  }
}
