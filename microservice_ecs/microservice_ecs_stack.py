from aws_cdk import Stack
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_autoscaling as autoscaling
from aws_cdk import aws_ecs as ecs
from aws_cdk.aws_ecs import PortMapping
from constructs import Construct


class MicroserviceEcsStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        # ! importing VPC
        self.vpc = ec2.Vpc.from_lookup(
            self, "monolith_stack_vpc", vpc_id='vpc-02286ac3ed54a0400')

        # ! creating cluster
        self.cluster = ecs.Cluster(
            self, "unicorn-shop-ecs-cluster", vpc=self.vpc)

        # ! importing security group
        self.web_server_sg = ec2.SecurityGroup.from_security_group_id(self, "webserver_sg", security_group_id="sg-0a39f7eb07425a7e8")

        # ! creating auto scaling group
        auto_scaling_group = autoscaling.AutoScalingGroup(
            self,
            "unicorn_shop_auto_scaling_group",
            vpc=self.vpc,
            instance_type=ec2.InstanceType("t2.micro"),
            machine_image=ecs.EcsOptimizedImage.amazon_linux2(),
            security_group=self.web_server_sg,
            associate_public_ip_address=True,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC),
            key_name="lnd_hobbit_db_key",
            desired_capacity=1
        )
        capacity_provider = ecs.AsgCapacityProvider(self, "capacity_provider", auto_scaling_group=auto_scaling_group)
        self.cluster.add_asg_capacity_provider(provider=capacity_provider)
        
        # ! creating task definition
        self.ec2_task_definition = ecs.Ec2TaskDefinition(self, 'unicorn_shop_task_def')
        # ! adding public registry
        container = self.ec2_task_definition.add_container("unicron_shop_container", 
                                                            image=ecs.ContainerImage.from_registry("public.ecr.aws/w0l8v3b9/app_modernization_workshop"),
                                                            memory_limit_mib=512
                                                        )

        # ! adding port mapping
        container.add_port_mappings(
            PortMapping(container_port=8080, host_port=8080))

        # ! creating service
        self.service = ecs.Ec2Service(self, "unicorn_ec2_service",
                                        task_definition=self.ec2_task_definition,
                                        cluster=self.cluster
                                    )
