# API Gateway for AgentCore API
resource "aws_api_gateway_rest_api" "copilot_api" {
  name        = "${var.project_name}-api"
  description = "Commercial Underwriter Co-Pilot AgentCore API"

  body = jsonencode({
    openapi = "3.0.0"
    info = {
      title   = "Commercial Underwriter Co-Pilot API"
      version = "1.0.0"
    }
    servers = [
      { url = "https://${var.api_domain}" }
    ]
    paths = {
      "/health" = {
        get = {
          operationId = "health_check"
          responses = {
            "200" = { description = "API is healthy" }
          }
        }
      }
      "/triage-submission" = {
        post = {
          operationId = "triage_submission"
          requestBody = {
            content = {
              "application/json" = {
                schema = { type = "object" }
              }
            }
          }
          responses = {
            "202" = { description = "Submission accepted" }
          }
          x-amazon-apigateway-integration = {
            type                 = "aws_proxy"
            httpMethod           = "POST"
            uri                  = aws_lambda_function.orchestration_agent.invoke_arn
            passthroughBehavior  = "when_no_match"
            contentHandling      = "CONVERT_TO_TEXT"
          }
        }
      }
    }
  })

  endpoint_configuration {
    types = ["REGIONAL"]
  }

  tags = {
    Name = "${var.project_name}-api"
  }
}

# API Gateway Deployment
resource "aws_api_gateway_deployment" "copilot_deployment" {
  rest_api_id = aws_api_gateway_rest_api.copilot_api.id

  depends_on = [
    aws_api_gateway_integration.orchestration_integration,
    aws_api_gateway_integration.status_integration
  ]
}

# Lambda permission for API Gateway
resource "aws_lambda_permission" "api_gateway_orchestration" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.orchestration_agent.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.copilot_api.execution_arn}/*/*"
}

# API Gateway Resource: /triage-submission
resource "aws_api_gateway_resource" "triage_submission" {
  rest_api_id = aws_api_gateway_rest_api.copilot_api.id
  parent_id   = aws_api_gateway_rest_api.copilot_api.root_resource_id
  path_part   = "triage-submission"
}

# API Gateway Method: POST /triage-submission
resource "aws_api_gateway_method" "triage_submission_post" {
  rest_api_id      = aws_api_gateway_rest_api.copilot_api.id
  resource_id      = aws_api_gateway_resource.triage_submission.id
  http_method      = "POST"
  authorization    = "AWS_IAM"
  request_models = {
    "application/json" = aws_api_gateway_model.triage_request.name
  }
}

# Integration: POST /triage-submission -> Orchestration Lambda
resource "aws_api_gateway_integration" "orchestration_integration" {
  rest_api_id      = aws_api_gateway_rest_api.copilot_api.id
  resource_id      = aws_api_gateway_resource.triage_submission.id
  http_method      = aws_api_gateway_method.triage_submission_post.http_method
  type             = "AWS_PROXY"
  integration_http_method = "POST"
  uri              = aws_lambda_function.orchestration_agent.invoke_arn
}

# Method Response
resource "aws_api_gateway_method_response" "orchestration_response" {
  rest_api_id    = aws_api_gateway_rest_api.copilot_api.id
  resource_id    = aws_api_gateway_resource.triage_submission.id
  http_method    = aws_api_gateway_method.triage_submission_post.http_method
  status_code    = "202"
  response_models = {
    "application/json" = aws_api_gateway_model.triage_request.name
  }
}

# Integration Response
resource "aws_api_gateway_integration_response" "orchestration_response" {
  rest_api_id       = aws_api_gateway_rest_api.copilot_api.id
  resource_id       = aws_api_gateway_resource.triage_submission.id
  http_method       = aws_api_gateway_method.triage_submission_post.http_method
  status_code       = "202"
  selection_pattern = ""

  response_templates = {
    "application/json" = ""
  }

  depends_on = [aws_api_gateway_integration.orchestration_integration]
}

# API Gateway Resource: /submission/{submission_id}
resource "aws_api_gateway_resource" "submission_resource" {
  rest_api_id = aws_api_gateway_rest_api.copilot_api.id
  parent_id   = aws_api_gateway_rest_api.copilot_api.root_resource_id
  path_part   = "submission"
}

resource "aws_api_gateway_resource" "submission_id_resource" {
  rest_api_id = aws_api_gateway_rest_api.copilot_api.id
  parent_id   = aws_api_gateway_resource.submission_resource.id
  path_part   = "{submission_id}"
}

# API Gateway Method: GET /submission/{submission_id}
resource "aws_api_gateway_method" "get_submission_status" {
  rest_api_id      = aws_api_gateway_rest_api.copilot_api.id
  resource_id      = aws_api_gateway_resource.submission_id_resource.id
  http_method      = "GET"
  authorization    = "AWS_IAM"

  request_parameters = {
    "method.request.path.submission_id" = true
  }
}

# Lambda for Status Retrieval
resource "aws_lambda_function" "status_retriever" {
  filename            = "lambda_functions/build/status_retriever.zip"
  function_name       = "${var.project_name}-status-retriever"
  role                = aws_iam_role.orchestration_agent_role.arn
  handler             = "index.handler"
  runtime             = "python3.11"
  timeout             = 30
  memory_size         = 256

  environment {
    variables = {
      S3_BUCKET = aws_s3_bucket.submissions_bucket.id
    }
  }

  tags = {
    Name = "${var.project_name}-status-retriever"
  }
}

# Lambda permission for status retriever
resource "aws_lambda_permission" "api_gateway_status" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.status_retriever.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.copilot_api.execution_arn}/*/*"
}

# Integration: GET /submission/{id} -> Status Retriever Lambda
resource "aws_api_gateway_integration" "status_integration" {
  rest_api_id      = aws_api_gateway_rest_api.copilot_api.id
  resource_id      = aws_api_gateway_resource.submission_id_resource.id
  http_method      = aws_api_gateway_method.get_submission_status.http_method
  type             = "AWS_PROXY"
  integration_http_method = "POST"
  uri              = aws_lambda_function.status_retriever.invoke_arn
}

# API Gateway Model: TriageRequest
resource "aws_api_gateway_model" "triage_request" {
  rest_api_id  = aws_api_gateway_rest_api.copilot_api.id
  name         = "TriageRequest"
  content_type = "application/json"

  schema = jsonencode({
    type = "object"
    properties = {
      document_uri = {
        type        = "string"
        description = "S3 URI of submission PDF"
        pattern     = "^s3://[a-z0-9.-]+/.*\\.pdf$"
      }
      insured_name = {
        type        = "string"
        description = "Known insured name"
      }
      policy_number = {
        type        = "string"
        description = "Policy number for cross-reference"
      }
      metadata = {
        type = "object"
      }
    }
    required = ["document_uri"]
  })
}

# API Gateway Authorizer (AWS_IAM)
resource "aws_api_gateway_account" "copilot" {
  cloudwatch_role_arn = aws_iam_role.api_gateway_role.arn

  depends_on = [aws_iam_role_policy.api_gateway_logging]
}

# IAM Role for API Gateway CloudWatch logging
resource "aws_iam_role" "api_gateway_role" {
  name = "${var.project_name}-api-gateway-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "apigateway.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy" "api_gateway_logging" {
  name   = "${var.project_name}-api-gateway-logging"
  role   = aws_iam_role.api_gateway_role.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
          "logs:DescribeLogGroups",
          "logs:DescribeLogStreams"
        ]
        Effect   = "Allow"
        Resource = "arn:aws:logs:*:*:*"
      }
    ]
  })
}

# API Gateway Stage with logging
resource "aws_api_gateway_stage" "copilot" {
  deployment_id = aws_api_gateway_deployment.copilot_deployment.id
  rest_api_id   = aws_api_gateway_rest_api.copilot_api.id
  stage_name    = var.environment

  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.api_gateway_logs.arn
    format = jsonencode({
      requestId        = "$context.requestId"
      status           = "$context.status"
      requestTime      = "$context.requestTime"
      httpMethod       = "$context.httpMethod"
      resourcePath     = "$context.resourcePath"
      sourceIp         = "$context.identity.sourceIp"
      protocol         = "$context.protocol"
      responseLength   = "$context.responseLength"
      integrationError = "$context.integrationErrorMessage"
      error            = "$context.error.message"
      integrationStatus = "$context.integration.status"
      integrationLatency = "$context.integration.latency"
      authorStatus     = "$context.authorizer.error"
    })
  }

  tags = {
    Name = "${var.project_name}-${var.environment}"
  }
}

# CloudWatch Log Group for API Gateway
resource "aws_cloudwatch_log_group" "api_gateway_logs" {
  name              = "/aws/apigateway/${var.project_name}"
  retention_in_days = var.log_retention_days

  tags = {
    Name = "${var.project_name}-api-gateway-logs"
  }
}

# REST API Domain Name (optional - for custom domain)
resource "aws_api_gateway_domain_name" "copilot" {
  count            = var.api_domain != "" && var.certificate_arn != "" ? 1 : 0
  domain_name      = var.api_domain
  certificate_arn  = var.certificate_arn

  endpoint_configuration {
    types = ["REGIONAL"]
  }
}

resource "aws_api_gateway_base_path_mapping" "copilot" {
  count       = var.api_domain != "" ? 1 : 0
  api_id      = aws_api_gateway_rest_api.copilot_api.id
  stage_name  = aws_api_gateway_stage.copilot.stage_name
  domain_name = aws_api_gateway_domain_name.copilot[0].domain_name
}

# Outputs
output "api_endpoint" {
  description = "API Gateway endpoint URL"
  value       = aws_api_gateway_stage.copilot.invoke_url
}

output "api_domain_name" {
  description = "Custom API domain (if configured)"
  value       = var.api_domain != "" ? aws_api_gateway_domain_name.copilot[0].domain_name : "Not configured"
}
