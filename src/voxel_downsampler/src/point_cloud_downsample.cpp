#include <rclcpp/rclcpp.hpp>
#include <sensor_msgs/msg/point_cloud2.hpp>
#include <pcl/point_cloud.h>
#include <pcl/point_types.h>
#include <pcl/filters/voxel_grid.h>
#include <pcl_conversions/pcl_conversions.h>
class VoxelDownsampler : public rclcpp::Node {
public:
VoxelDownsampler() : Node("voxel_downsampler") {
double leaf;
// Declare parameters
declare_parameter("leaf_size", 0.10);
declare_parameter("input_topic", std::string("/j100_0882/sensors/lidar3d_0/points"));
declare_parameter("output_topic", std::string("/points_voxel"));
get_parameter("leaf_size", leaf);
get_parameter("input_topic", input_topic_);
get_parameter("output_topic", output_topic_);
leaf_size_ = static_cast<float>(leaf);
// Create subscriber and publisher
sub_ = create_subscription<sensor_msgs::msg::PointCloud2>(input_topic_,
rclcpp::SensorDataQoS(),
std::bind(&VoxelDownsampler::cb, this, std::placeholders::_1));
pub_ = create_publisher<sensor_msgs::msg::PointCloud2>(output_topic_, 10);
RCLCPP_INFO(get_logger(), "VoxelDownsampler listening on %s -> %s (leaf=%.3f m)",
input_topic_.c_str(), output_topic_.c_str(), leaf_size_);
}
private:
// Callback function to process incoming data
void cb(const sensor_msgs::msg::PointCloud2::SharedPtr msg) {
pcl::PCLPointCloud2::Ptr cloud_in(new pcl::PCLPointCloud2());
pcl::PCLPointCloud2::Ptr cloud_out(new pcl::PCLPointCloud2());
// Convert ROS message to PCL data type
pcl_conversions::toPCL(*msg, *cloud_in);
// Configure and apply the voxel grid filter
pcl::VoxelGrid<pcl::PCLPointCloud2> vg;
vg.setInputCloud(cloud_in);
vg.setLeafSize(leaf_size_, leaf_size_, leaf_size_);
vg.filter(*cloud_out);
// Convert filtered PCL data back to ROS message and publish
sensor_msgs::msg::PointCloud2 out;
pcl_conversions::fromPCL(*cloud_out, out);
out.header = msg->header;
pub_->publish(out);
}
rclcpp::Subscription<sensor_msgs::msg::PointCloud2>::SharedPtr sub_;
rclcpp::Publisher<sensor_msgs::msg::PointCloud2>::SharedPtr pub_;
std::string input_topic_, output_topic_;
float leaf_size_;
};
int main(int argc, char **argv) {
rclcpp::init(argc, argv);
rclcpp::spin(std::make_shared<VoxelDownsampler>());
rclcpp::shutdown();
return 0;
}