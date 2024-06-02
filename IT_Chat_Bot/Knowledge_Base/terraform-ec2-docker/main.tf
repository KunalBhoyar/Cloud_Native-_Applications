provider "aws" {
  region = var.region # Replace with your desired region
}

resource "aws_key_pair" "deployer" {
  key_name   = "deployer-key"
  public_key = file(var.public_key_path)  # Replace with the path to your public key
}

resource "aws_security_group" "allow_ssh" {
  name_prefix = "allow_ssh"

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }


 ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }


  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_instance" "web" {
  ami           = "ami-0bb84b8ffd87024d8"  # Replace with your preferred AMI ID
  instance_type = "t2.micro"
  key_name      = aws_key_pair.deployer.key_name
  security_groups = [
    aws_security_group.allow_ssh.name
  ]

  root_block_device {
    volume_size = 16
  }

  user_data = <<-EOF
              #!/bin/bash
              sudo yum update -y
              sudo yum install docker -y
              sudo systemctl start docker
              sudo systemctl enable docker

              # Add the current user to the Docker group to avoid permission issues
              sudo usermod -aG docker ec2-user

              # Reboot the instance to apply group membership changes
              sudo shutdown -r +1 "Rebooting to apply Docker group changes"
              EOF

  tags = {
    Name = "DockerInstance"
  }




   provisioner "local-exec" {
    command = <<-EOC
      echo "Waiting for instance to reboot..."
      sleep 120  # Adjust this based on the expected reboot time
      while ! nc -z ${aws_instance.web.public_ip} 22; do
        sleep 5
      done
      echo "Instance is back online."
      EOC
  }
   



  provisioner "remote-exec" {
    inline = [
      "sleep 60", # Wait for the instance to reboot
      "sudo docker login -u ${var.docker_username} -p ${var.docker_password}",
      "sudo docker pull kbhoyar28/final-knowledgebase-jsr:latest",
      "sudo docker run -d -p 80:80 kbhoyar28/final-knowledgebase-jsr:latest"
    ]

    connection {
      type     = "ssh"
      user     = "ec2-user"
      private_key = file("~/.ssh/id_rsa")  # Use the private key here
      host     = self.public_ip
    }
  }
}

output "instance_ip" {  
  value = aws_instance.web.public_ip
}
