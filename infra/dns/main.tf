provider "aws" {
  region = "eu-west-3"
}

data "aws_eks_cluster" "cluster" {
  name = "anoti-cluster"
}

data "aws_iam_openid_connect_provider" "eks" {
  url = data.aws_eks_cluster.cluster.identity[0].oidc[0].issuer
}

resource "aws_iam_role" "external_dns" {
  name = "EKSClusterExternalDNSRole"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Action = "sts:AssumeRoleWithWebIdentity",
        Effect = "Allow",
        Principal = {
          Federated = data.aws_iam_openid_connect_provider.eks.arn
        }
      }
    ]
  })
}

resource "aws_iam_role_policy" "external_dns_policy" {
  name = "ClusterExternalDNSPolicy"
  role = aws_iam_role.external_dns.id

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Action = [
          "route53:ChangeResourceRecordSets"
        ],
        Effect   = "Allow",
        Resource = "arn:aws:route53:::hostedzone/*"
      },
      {
        Action = [
          "route53:ListHostedZones",
          "route53:ListResourceRecordSets"
        ],
        Effect   = "Allow",
        Resource = "*"
      }
    ]
  })
}

output "external_dns_role_arn" {
  value = aws_iam_role.external_dns.arn
}
