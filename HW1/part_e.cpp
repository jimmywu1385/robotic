#include "Aria.h"
#include<stdio.h>
#include<math.h>
#include<iostream>
#define PI acos(-1)
/*
c++ -fPIC -g -Wall -I/usr/local/Aria/include part_e.cpp -o part_e -L/usr/local/Aria/lib -lAria -lpthread -ldl -lrt
*/
int main(int argc, char** argv)
{
  Aria::init();
  ArArgumentParser parser(&argc, argv);

  parser.loadDefaultArguments();

  ArRobot robot;

  ArRobotConnector robotConnector(&parser, &robot);

  if (!robotConnector.connectRobot())
  {
    if (!parser.checkHelpAndWarnUnparsed())
    {
      ArLog::log(ArLog::Terse, "Could not connect to robot, will not have parameter file so options displayed later may not include everything");
    }
    else
    {
      ArLog::log(ArLog::Terse, "Error, could not connect to robot.");
      Aria::logOptions();
      Aria::exit(1);
    }
  }

  if(!robot.isConnected())
  {
    ArLog::log(ArLog::Terse, "Internal error: robot connector succeeded but ArRobot::isConnected() is false!");
  }

  ArLaserConnector laserConnector(&parser, &robot, &robotConnector);

  if (!Aria::parseArgs())
  {    
    Aria::logOptions();
    Aria::exit(1);
    return 1;
  }

  ArSonarDevice sonarDev;

  robot.addRangeDevice(&sonarDev);


  double x=0.0,y=0.0,theta=0.0;

  printf("input>>");
  scanf("%lf%lf%lf",&x, &y, &theta);
  x*=1000;
  y*=1000;
  theta*=(180.0/PI);

  robot.comInt(ArCommands::ENABLE, 1);
  robot.runAsync(false);

  if (!laserConnector.connectLasers(false, false, true))
  {
     printf("Warning: Could not connect to laser(s). Set LaserAutoConnect to false in this robot's individual parameter file to disable laser connection.\n");
  }

  ArRobotPacket pkt;
  pkt.setID(ArCommands::SIM_SET_POSE);
  pkt.uByteToBuf(0);
  pkt.byte4ToBuf(5090);
  pkt.byte4ToBuf(3580);
  pkt.byte4ToBuf(3093.97);
  pkt.finalizePacket();
  robot.getDeviceConnection()->write(pkt.getBuf(),pkt.getLength());
  robot.moveTo(ArPose(5090, 3500, 3093.97));

  ArUtil::sleep(1000);

  robot.lock();
  robot.setHeading(0);
  robot.unlock();

while(1)
{
  robot.lock();
   if(robot.isHeadingDone())
   {
      robot.unlock();
      break;
   }
  robot.unlock();
    ArUtil::sleep(100);
}

  robot.lock();
  robot.move(x-5090);
  robot.unlock();

while(1)
{
  robot.lock();
   if(robot.isMoveDone())
   {
      robot.unlock();
      break;
   }
    robot.unlock();
    ArUtil::sleep(50);
}


  robot.lock();
  robot.setHeading(90);
  robot.unlock();


while(1)
{
  robot.lock();
   if(robot.isHeadingDone())
   {
      robot.unlock();
      break;
   }
  robot.unlock();
  ArUtil::sleep(100);
}

  robot.lock();
  robot.move(y-3580);
  robot.unlock();

while(1)
{
  robot.lock();
   if(robot.isMoveDone())
   {
      robot.unlock();
      break;
   }
    robot.unlock();
    ArUtil::sleep(50);
}

  robot.lock();
  robot.setHeading(theta);
  robot.unlock();

  robot.waitForRunExit();
  Aria::exit(0);

  return 0;
}