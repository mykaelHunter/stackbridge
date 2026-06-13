output "instance_id" {
  description = "EC2 instance ID"
  value       = aws_instance.app.id
}

output "private_ip" {
  description = "Private IP of the instance"
  value       = aws_instance.app.private_ip
}

output "security_group_id" {
  description = "ID of the app security group — pass to database module to allow DB access"
  value       = aws_security_group.app.id
}
