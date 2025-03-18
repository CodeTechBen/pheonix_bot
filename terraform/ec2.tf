data "aws_vpc" "bot-vpc" {
    id = "vpc-07cb9502c2c54fee2"
}

data "aws_subnet" "public-subnet" {
    vpc_id = data.aws_vpc.bot-vpc.id
    cidr_block = "172.31.16.0/20"
}

resource "aws_security_group" "ec2-sg" {
    name = "ben-pheonix-ec2-sec-group"
    vpc_id = data.aws_vpc.bot-vpc.id

    ingress {
        from_port = 22
        to_port = 22
        protocol = "tcp"
        cidr_blocks = ["0.0.0.0/0"]
    }

    egress {
        from_port = 0
        to_port = 0
        protocol = "-1"
        cidr_blocks = ["0.0.0.0/0"]
    }
}

resource "aws_instance" "bot-ec2" {
    ami = "ami-09a2a0f7d2db8baca"
    instance_type = "t2.nano"
    
    subnet_id = data.aws_subnet.public-subnet.id
    security_groups = [aws_security_group.ec2-sg.id]

    associate_public_ip_address = true

    key_name = "ben-pheonix-bot-kp"

    tags = {
      Name = "ben-pheonix-ec2"
    }
}