
# Security Group for PostgreSQL EC2 instance
resource "aws_security_group" "postgres-sg" {
  name   = "ben-pheonix-postgres-sec-group"
  vpc_id = data.aws_vpc.bot-vpc.id

  # Allow inbound traffic on port 5432 (PostgreSQL)
  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = ["172.31.0.0/16"]
  }

   ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = ["86.129.86.154/32"]
  }

  # Allow SSH from your public IP
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["${var.public_ip}/32"]
  }

  # Allow outbound traffic
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}


# PostgreSQL EC2 instance
resource "aws_instance" "postgres-ec2" {
  ami                    = "ami-09a2a0f7d2db8baca"
  instance_type          = "t2.micro"
  subnet_id              = data.aws_subnet.public-subnet.id
  security_groups        = [aws_security_group.postgres-sg.id]
  associate_public_ip_address = true
  key_name               = "ben-pheonix-bot-kp"
  tags = {
    Name = "ben-pheonix-postgres-ec2"
  }

}

# Output the private IP of the PostgreSQL EC2 instance
output "postgres_private_ip" {
  value = aws_instance.postgres-ec2.private_ip
}
