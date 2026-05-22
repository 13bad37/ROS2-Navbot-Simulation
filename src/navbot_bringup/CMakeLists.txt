cmake_minimum_required(VERSION 3.8)
project(navbot_bringup)

find_package(ament_cmake REQUIRED)

install(DIRECTORY
  config
  launch
  maps
  params
  worlds
  resource
  DESTINATION share/${PROJECT_NAME}
)

if(BUILD_TESTING)
  find_package(ament_cmake_pytest REQUIRED)
  ament_add_pytest_test(test_launch_options test/test_launch_options.py)
endif()

ament_package()
