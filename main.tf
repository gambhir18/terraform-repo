resource "aws_vpc" "Demo_VPC" {
  cidr_block = "10.4.0.0/16"
  tags = {
    Name =  "Demo_VPC"
  }
}
