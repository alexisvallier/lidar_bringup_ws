from setuptools import find_packages, setup
from setuptools import setup
import os
from glob import glob

package_name = 'lidar_tf2_mocap_py'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py'))
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='vallia2',
    maintainer_email='vallia2@todo.todo',
    description='TODO: Package description',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
        	'lidar_tf2_mocap_py = lidar_tf2_mocap_py.lidar_tf2_mocap_py:main',
        ],
    },
)
