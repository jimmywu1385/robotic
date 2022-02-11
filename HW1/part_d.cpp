#include "Aria.h"
#include<stdio.h>
#include<iostream>
/*
c++ -fPIC -g -Wall -I/usr/local/Aria/include part_d.cpp -o part_d -L/usr/local/Aria/lib -lAria -lpthread -ldl -lrt
*/
void accelerate(ArRobot *robot, int *speed)
{
  *speed+=10;
  robot->setVel(*speed);
}
void decelerate(ArRobot *robot, int *speed)
{
  *speed-=10;
  robot->setVel(*speed);
}
void turn_left(ArRobot *robot, int *rspeed)
{
  *rspeed=8;
  robot->setRotVel(*rspeed);
}
void turn_right(ArRobot *robot, int *rspeed)
{
  *rspeed=-8;
  robot->setRotVel(*rspeed);
}
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
  
  ArKeyHandler keyHandler;
  Aria::setKeyHandler(&keyHandler);

  robot.attachKeyHandler(&keyHandler);

  robot.addRangeDevice(&sonarDev);

  robot.runAsync(true);

  if (!laserConnector.connectLasers(false, false, true))
  {
     printf("Warning: Could not connect to laser(s). Set LaserAutoConnect to false in this robot's individual parameter file to disable laser connection.\n");
  }
  
  int speed=0;
  int rspeed=0;

  ArUtil::sleep(1000);

  robot.lock();

  keyHandler.addKeyHandler(256, new ArGlobalFunctor2<ArRobot*, int*>(&accelerate, &robot, &speed));
  keyHandler.addKeyHandler(257, new ArGlobalFunctor2<ArRobot*, int*>(&decelerate, &robot, &speed));
  keyHandler.addKeyHandler(258, new ArGlobalFunctor2<ArRobot*, int*>(&turn_left, &robot, &rspeed));
  keyHandler.addKeyHandler(259, new ArGlobalFunctor2<ArRobot*, int*>(&turn_right, &robot, &rspeed));

  robot.comInt(ArCommands::ENABLE, 1);

  robot.unlock();

  double radius=robot.getRobotRadius();
  double myStopDistance=1000;
  
  while(true){
    robot.setVel(speed*0.2);
    double range = sonarDev.currentReadingPolar(-70, 70)-radius;
    if (range < myStopDistance)
  {
    robot.setVel(0);
  }

    robot.setRotVel(0);
    ArUtil::sleep(800);
  }
  robot.waitForRunExit();
  Aria::exit(0);

  return 0;
}