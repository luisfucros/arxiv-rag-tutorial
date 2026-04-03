
output "nlb_dns_name" {
  value       = aws_lb.qdrant.dns_name
  description = "Private NLB DNS for Qdrant (REST/gRPC clients use host + ports 6333/6334)"
}

output "nlb_arn" {
  value       = aws_lb.qdrant.arn
  description = "Qdrant internal NLB ARN"
}
