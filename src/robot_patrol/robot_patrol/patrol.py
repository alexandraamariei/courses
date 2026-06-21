#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from geometry_msgs.msg import TwistStamped
from sensor_msgs.msg import LaserScan

class Patrol(Node):

    def __init__(self):
        super().__init__('patrol_node')

        self.scan_sub = self.create_subscription(
            LaserScan,
            '/scan',
            self.laser_callback,
            qos_profile_sensor_data)

        self.cmd_pub = self.create_publisher(
            TwistStamped,
            '/cmd_vel', 
            5)

        # TIMERUL A FOST STERS DE AICI COMPLET!

        self.cmd = TwistStamped()
        self.cmd.twist.linear.x = 0.0
        self.cmd.twist.angular.z = 0.0

        self.min_distance = 0.55
        self.side_threshold = 0.15

        self.left_side = 0.0
        self.front = 0.0
        self.right_side = 0.0
        
    def laser_callback(self, msg: LaserScan):
        max_idx = len(msg.ranges) - 1
        self.front = msg.ranges[0]
        
        if max_idx < 2000:
            self.left_side = msg.ranges[int(max_idx * 0.25)]
            self.right_side = msg.ranges[int(max_idx * 0.75)]
        else:
            self.left_side = msg.ranges[748]
            self.right_side = msg.ranges[2246]
            
        self.get_logger().info('Obstacol fata la: "%s" metri' % str(self.front)) 
        
        # TRUCUL MAGIC: Apelam miscarea fix in momentul in care primim laserul!
        # Astfel, ocolim orice problema legata de ceasul ROS 2 sau Gazebo.
        self.motion()

    def motion(self):
        self.get_logger().info('--- Calculez miscarea! ---')
        linear_vel = 0.2 
        angular_vel = 0.2 # Rotire mai lina

        # Filtram valorile infinite sau "0.0" (in simulatoare, cand laserul bate in gol da 0.0 sau inf)
        if self.front == 0.0 or str(self.front) == 'inf':
            self.front = 3.5

        if self.left_side < self.side_threshold and self.front > self.min_distance:
            self.get_logger().warning('Obstacol stanga! Vireaza dreapta!!')
            self.cmd.twist.linear.x = linear_vel * 0.5
            self.cmd.twist.angular.z = -angular_vel
        elif self.right_side < self.side_threshold and self.front > self.min_distance:
            self.get_logger().warning('Obstacol dreapta! Vireaza stanga!!')
            self.cmd.twist.linear.x = linear_vel * 0.5
            self.cmd.twist.angular.z = angular_vel
        elif self.front > self.min_distance:
            self.get_logger().info('Cale libera. Moving forward!!')
            self.cmd.twist.linear.x = linear_vel
            self.cmd.twist.angular.z = 0.0
        else:
            self.get_logger().error('Obstacol in fata! Stop and rotate!!')
            # L-am scos din "balbaiala". Acum se va roti intotdeauna constant spre stanga 
            # pana cand vede din nou calea libera, in loc sa oscileze haotic stanga-dreapta
            self.cmd.twist.linear.x = 0.0
            self.cmd.twist.angular.z = angular_vel

        self.cmd.header.stamp = self.get_clock().now().to_msg()
        self.cmd.header.frame_id = ''

        self.cmd_pub.publish(self.cmd)

    def compare_sides(self, left, right):
        return left >= right 

def main(args=None):
    rclpy.init(args=args)
    patrol_node = Patrol()
    try:
        rclpy.spin(patrol_node)
    except KeyboardInterrupt:
        pass
    finally:
        patrol_node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()

if __name__ == '__main__':
    main()