from launch import LaunchDescription
from launch.event_handlers import OnProcessStart
from launch.launch_description_sources import PythonLaunchDescriptionSource
from ament_index_python.packages import get_package_share_directory
from launch_ros.actions import Node, LifecycleNode
from launch.substitutions import LaunchConfiguration
from launch.actions import (
    RegisterEventHandler,
    TimerAction,
    SetEnvironmentVariable,
    DeclareLaunchArgument,
    EmitEvent,
)
from launch_ros.events.lifecycle import ChangeState
import launch
import lifecycle_msgs.msg

import os

def generate_launch_description():

    # Parameters
    params_file_path = os.path.join(get_package_share_directory(
      'mocap4r2_optitrack_driver'), 'config', 'mocap4r2_optitrack_driver_params.yaml')

    # Downsampler node
    node_1 = Node(
        package='voxel_downsampler',
        executable='point_cloud_downsample',
        name='point_cloud_downsample',
        output='screen'
    )

    # Optitrack node
    driver_node = LifecycleNode(
        name='mocap4r2_optitrack_driver_node',
        namespace=LaunchConfiguration('namespace'),
        package='mocap4r2_optitrack_driver',
        executable='mocap4r2_optitrack_driver_main',
        output='screen',
        parameters=[LaunchConfiguration('config_file')],
    )

    driver_configure_trans_event = EmitEvent(
        event=ChangeState(
            lifecycle_node_matcher=launch.events.matchers.matches_action(driver_node),
            transition_id=lifecycle_msgs.msg.Transition.TRANSITION_CONFIGURE,
        )
    )

    driver_activate_trans_event = EmitEvent(
        event = ChangeState(
            lifecycle_node_matcher = launch.events.matchers.matches_action(driver_node),
            transition_id = lifecycle_msgs.msg.Transition.TRANSITION_ACTIVATE,
        )
    )

    # Transform node
    node_3 = Node(
        package='lidar_tf2_mocap_py',
        executable='lidar_tf2_mocap_py',
        name='lidar_tf2_mocap_py',
        output='screen'
    )

    # Create the launch description and populate
    ld = LaunchDescription()

    ld.add_action(SetEnvironmentVariable(
        'RCUTILS_CONSOLE_STDOUT_LINE_BUFFERED', '1'
    ))
    ld.add_action(DeclareLaunchArgument('namespace', default_value=''))
    ld.add_action(DeclareLaunchArgument('config_file', default_value=params_file_path))

    # start downsampler
    ld.add_action(node_1)
    # start optitrack node after
    ld.add_action(
        RegisterEventHandler(
            OnProcessStart(
                target_action=node_1,
                on_start=[driver_node]
            )
        )
    )
    
    # Configure OptiTrack after it starts
    ld.add_action(
        RegisterEventHandler(
            OnProcessStart(
                target_action=driver_node,
                on_start=[
                    TimerAction(period=2.0, actions=[driver_configure_trans_event])
                ]
            )
        )
    )

    # Activate OptiTrack after configure
    ld.add_action(
        RegisterEventHandler(
            OnProcessStart(
                target_action=driver_node,
                on_start=[
                    TimerAction(period=4.0, actions=[driver_activate_trans_event])
                ]
            )
        )
    )

    ld.add_action(
        RegisterEventHandler(
            OnProcessStart(
                target_action=driver_node,
                on_start=[
                    TimerAction(period=6.0, actions=[node_3])
                ]
            )
        )
    )

    return ld
