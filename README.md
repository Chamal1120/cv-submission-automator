# CV submission automater

CV submission automater is a job application processing pipeline developed for the Metana Software Enginnering Intern (RnD) assignment. This automates the complete pipeline from the:
1. Candidate submitting CV, 
2. Extracting relevant details from it
4. Saving them in a google sheet
5. Sending a `processing done` response to the recruting company
6. And sending a follow up email back to the candidate

## Tech Stack

1. Frontend - React (bootsrapped with vite)
2. Backend - Python (Lambda function)
3. Middleman - Python (Lambda function)
4. Infrastructure  - Amazon Web Services (AWS)
5. SendGrid - Email Service
6. Google sheets api - To write to google sheets
7. CI/CD - AWS Codepipeline and Codebuild
8. Infra-management - Terraform
9. VCS - Git and Github
10. Testing - Pytest, Vitest (WIP)

## Deployment Instructions

#### Prerequisites

1. AWS IAM user with following permissions

```
AmazonAPIGatewayAdministrator
AmazonS3FullAccess
AmazonSSMFullAccess
AWSCodeBuildAdminAccess
AWSCodePipeline_FullAccess
AWSLambda_FullAccess
CloudWatchLogsFullAccess
IAMFullAccess
CodeStarAccessCustom (refer the custom policy)
KMSAccessCustom (refer the custom policy)
```

##### Codestar custom inline policy
```
{
	"Version": "2012-10-17",
	"Statement": [
		{
			"Sid": "ConnectionsFullAccess",
			"Effect": "Allow",
			"Action": [
				"codeconnections:CreateConnection",
				"codeconnections:DeleteConnection",
				"codeconnections:UseConnection",
				"codeconnections:GetConnection",
				"codeconnections:ListConnections",
				"codeconnections:ListInstallationTargets",
				"codeconnections:GetInstallationUrl",
				"codeconnections:StartOAuthHandshake",
				"codeconnections:UpdateConnectionInstallation",
				"codeconnections:GetIndividualAccessToken",
				"codeconnections:TagResource",
				"codeconnections:ListTagsForResource",
				"codeconnections:UntagResource"
			],
			"Resource": "*"
		}
	]
}
```

##### KMS custom inline policy
```
{
	"Version": "2012-10-17",
	"Statement": [
		{
			"Effect": "Allow",
			"Action": [
				"kms:Encrypt",
				"kms:Decrypt",
				"kms:GenerateDataKey*",
				"kms:DescribeKey",
				"kms:CreateKey",
				"kms:ListKeys",
				"kms:CreateAlias"
			],
			"Resource": "*"
		}
	]
}
```

#### Steps

1. Fork, clone and cd into the repo:
```bash
git clone "your-fork's-git-url"
cd <your-fork's-name>
```

2. zip backend and middleman codes:
```bash
cd backend
mkdir package
uv pip install --target=package -r requirements.txt
cp -r lambda_function.py models/ utils/ package/
cd package
zip -r ..//lambda_function.zip && cd ../..

cd middleman 
mkdir package
uv pip install --target=package -r requirements.txt
cp -r get_presigned_url.py models/ utils/ package/
cd package
zip -r ..//lambda_get_presigned_url.zip && cd ..
```

2. Go to terraform dir and create the variables.tfvars file as follows:

```bash
cd ..
cd terraform
```

```txt
# terraform.tfvars
aws_region           = "preffered-region"
github_owner         = "github-user-name-of-the-git-repo"
github_repo          = "fork's-name"
github_token         = "gh-PAT-token"
github_webhook_secret = "put-a-unique-password-here"
```

2. Init terraform:

```bash
terraform init
```
4. Deploy the infra:
```bash
terraform validate
terraform plan --out="tfplan"
terraform apply "tfplan"
```

4. Go to AWS Codepipeline console > settings > connections and verify the codestar connection.

5. Push the code to online git repo:
```bash
git push -u origin main
```

## Thank You
