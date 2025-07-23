output "vpc_id" {
  description = "The ID of the VPC"
  value       = aws_vpc.main.id
}

output "public_subnet_id" {
  description = "The ID of the first public subnet"
  value       = aws_subnet.public.id
}

output "public_subnet_id_2" {
  description = "The ID of the second public subnet"
  value       = aws_subnet.public_2.id
}

output "private_subnet_id" {
  description = "The ID of the first private subnet"
  value       = aws_subnet.private.id
}

output "private_subnet_id_2" {
  description = "The ID of the second private subnet"
  value       = aws_subnet.private_2.id
}

output "nat_gateway_ip" {
  description = "The public IP address of the NAT Gateway"
  value       = aws_eip.nat.public_ip
} 