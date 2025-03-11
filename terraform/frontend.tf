# Buidspec for frontend build
locals {
    buildspec_frontend = <<EOF
version: 0.2
phases:
  install:
    runtime-versions:
      nodejs: 20
    commands:
      - cd frontend
      - echo "Installing deps"
      - npm install
  build:
    commands:
      - echo "Building frontend"
      - npm run build
      - aws s3 sync dist/ s3://${aws_s3_bucket.frontend_bucket.bucket}/ --acl public-read
EOF
}

# Frontend S3 Bucket for React App
resource "aws_s3_bucket" "frontend_bucket" {
  bucket_prefix = "cv-parser-frontend-" 
  force_destroy = true
}

resource "aws_s3_bucket_ownership_controls" "frontend_bucket_ownership" {
  bucket = aws_s3_bucket.frontend_bucket.id
  rule {
    object_ownership = "BucketOwnerPreferred"
  }
}

resource "aws_s3_bucket_acl" "frontend_bucket_acl" {
  bucket = aws_s3_bucket.frontend_bucket.id
  acl    = "private"
  depends_on = [aws_s3_bucket_ownership_controls.frontend_bucket_ownership]
}

resource "aws_s3_bucket_public_access_block" "frontend_bucket_access" {
  bucket = aws_s3_bucket.frontend_bucket.id
  block_public_acls       = false
  block_public_policy     = false
  ignore_public_acls      = false
  restrict_public_buckets = false
}

resource "aws_s3_bucket_policy" "frontend_public_read" {
  bucket = aws_s3_bucket.frontend_bucket.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect    = "Allow"
        Principal = "*"
        Action    = "s3:GetObject"
        Resource  = "${aws_s3_bucket.frontend_bucket.arn}/*"
      }
    ]
  })
  depends_on = [aws_s3_bucket_public_access_block.frontend_bucket_access]
}

resource "aws_s3_bucket_website_configuration" "frontend_website" {
  bucket = aws_s3_bucket.frontend_bucket.id
  index_document {
    suffix = "index.html"
  }
  error_document {
    key = "index.html"
  }
}

# Output the bucket name and website URL
output "frontend_bucket_name" {
  value = aws_s3_bucket.frontend_bucket.bucket
}

output "frontend_website_url" {
  value = "http://${aws_s3_bucket.frontend_bucket.bucket}.s3-website-${var.aws_region}.amazonaws.com"
}

# CodeBuild for Frontend
resource "aws_codebuild_project" "frontend_build" {
  name          = "cv-parser-frontend-build"
  service_role  = aws_iam_role.codebuild_role.arn
  artifacts { type = "NO_ARTIFACTS" }
  environment {
    compute_type = "BUILD_LAMBDA_1GB"
    image        = "aws/codebuild/amazonlinux-x86_64-lambda-standard:nodejs20"
    type         = "LINUX_LAMBDA_CONTAINER"
  }
  source {
    type            = "GITHUB"
    location        = "https://github.com/${var.github_owner}/${var.github_repo}.git"
    git_clone_depth = 1
    buildspec        = local.buildspec_frontend
  }
}

# CodePipeline for Frontend
resource "aws_codepipeline" "frontend_pipeline" {
  name     = "cv-parser-frontend-pipeline"
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
      configuration = { ProjectName = aws_codebuild_project.frontend_build.name }
    }
  }
}
