<div align="center">

# CV submission automater

-- An Open Source Automated CV Processing Pipeline --

</div>

## Why this exists?
So many start up companies that I applied didn't have a proper CV processing pipeline which makes candidates un-aware of what happened to their application and sometimes recruiter doesn't even have a proper way to query these applications which makes this process tedious for both candidates and recruiters.

This aims to solve that issue by providing a configurable CV processing pipeline for companies that doesn't have time to create their own from scratch. So if you're a recruiter, you can set this up in your infrastructure (preferably AWS) in seconds and start managing those 1000+ CVs flowing to you like a boss.

Plus this is Open Source and licensed under MIT, So you can do whatever the customization you want on top of this and use.

## Little bit about this idea
Initially this was developed as an Internship assignment for Metana Intern Software Engineer position. Then fell in love with this idea and asked from them if I could use this and develop it into a configurable open source application which anyone can use.

* So, huge thank to **[Metana Company](https://metana.io)** for allowing me to develop this into a FOSS product.

## What this does
1. Collects candidates' CVs from an intuitive frontend.
2. Extracts relevant details (via RegEx).
3. Appends data to a recruiter’s Google Sheet.
4. Notifies the recruiter once processing is complete.
5. Sends follow-up emails to candidates.

## Upcoming improvements (Help is needed)
1. Sending follow up emails in candidates' convenient timezone defined by the recruiters.
2. Adding a method to keep track on the CV progress and send mails to candidates when there is an update. 
2. Adding AI based CV detials extraction as an option for the recuiters.
3. Implement an MCP (Model-Context-Protocol) to bridge the result spreadsheet with an AI chatbot, so the recruiters can query the candidates CVs using human langauge instead of manually searching through the spreadsheet.

## Technologies used
1. **Frontend** - React (bootsrapped with vite)
2. **Backend** - Python (Lambda function)
3. **Middleman** - Python (Lambda function)
4. **Infrastructure**  - Amazon Web Services (AWS)
5. **Email Service** - SendGrid, AWS SES
6. **Google sheets api** - To write to google sheets
7. **CI/CD** - AWS Codepipeline and Codebuild
8. **Infra-management** - Terraform
9. **VCS** - Git and GitHub
10. **Testing** - Pytest

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

## Contributing
This is an Open Source Project licensed under **MIT License** and any contribution is warmly welcome.

