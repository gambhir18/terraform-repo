resource "aws_vpc" "Sunny_VPC" {
  cidr_block = "10.4.0.0/16"
  tags = {
    Name =  "Sunny_VPC"
  }
}
