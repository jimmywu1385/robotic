#include <opencv2/opencv.hpp>
#include <iostream>
#include <stack>
#include <math.h>
#include <string>

using namespace std;
using namespace cv;
typedef pair<double, double> pii;

void Draw(Mat regionMap, int regionNum, Mat& Image, vector<pii>& centers, vector<double>& angles){

	for (int i = 1; i < regionNum+1; i++){
		int area = 0;
		pii center{0, 0};
		for (int r = 0; r < regionMap.rows; r++)
			for (int c = 0; c < regionMap.cols; c++)
				if (regionMap.at<int>(r, c) == i){
					area++;
					center.first += r;
					center.second += c;
				}

		if (area < 200)
			continue;
		center.first /= area;
		center.second /= area;

		double m11 = 0;
		double m20 = 0;
		double m02 = 0;

		for (int r = 0; r < regionMap.rows; r++)
			for (int c = 0; c < regionMap.cols; c++)
				if (regionMap.at<int>(r, c) == i){
					m11 += pow((r - center.first), 1) * pow((c - center.second), 1);
					m20 += pow((r - center.first), 2) * pow((c - center.second), 0);
					m02 += pow((r - center.first), 0) * pow((c - center.second), 2);
				}
		double angle = 0.5*atan2(2*m11, m20-m02);
		double a = angle;
		if (angle < 0) {
			a += CV_PI;
		}
		centers.push_back(make_pair(center.first, center.second));
		angles.push_back(a);

		Point A, B;
		int length = 150;
		A.x = (int)round(center.second - length * sin(angle));
		A.y = (int)round(center.first - length * cos(angle));
		B.x = (int)round(center.second + length * sin(angle));
		B.y = (int)round(center.first + length * cos(angle));
		
		line(Image, A, B, Scalar(0, 0, 255), 3);
		circle(Image, Point(center.second, center.first), 5, Scalar(0, 0, 0), FILLED, LINE_8);
	}
}

int main(int argc, char** argv){
	string filename;
    cout << "Please input filename : ";
    cin >> filename;
    Mat Image, WorkImage, regionMap;

    Image = imread(filename);
	WorkImage = imread(filename, 0);;
    
    GaussianBlur(WorkImage, WorkImage, Size(3, 3), 0, 0);
    threshold(WorkImage, WorkImage, 0, 255, THRESH_OTSU);

    int regionNum = 0;

	regionMap = Mat::zeros(WorkImage.rows, WorkImage.cols, CV_32S);
	stack<pii> index;

	for (int i = 0; i < WorkImage.rows; i++)
		for (int j = 0; j < WorkImage.cols; j++)
			if (WorkImage.at<uchar>(i, j) == 255 && regionMap.at<int>(i, j) == 0) {
				regionNum++;
				index.push(make_pair(i, j));
				regionMap.at<int>(i, j) = regionNum;
				while (index.size() != 0) {
					pii now = index.top();
					index.pop();
					if (WorkImage.at<uchar>(now.first, now.second + 1) == 255 && regionMap.at<int>(now.first, now.second + 1) == 0) {
						index.push(make_pair(now.first, now.second + 1));
						regionMap.at<int>(now.first, now.second + 1) = regionNum;
					}
					if (WorkImage.at<uchar>(now.first + 1, now.second) == 255 && regionMap.at<int>(now.first + 1, now.second) == 0) {
						index.push(make_pair(now.first + 1, now.second));
						regionMap.at<int>(now.first + 1, now.second) = regionNum;
					}
					if (WorkImage.at<uchar>(now.first, now.second - 1) == 255 && regionMap.at<int>(now.first, now.second - 1) == 0) {
						index.push(make_pair(now.first, now.second - 1));
						regionMap.at<int>(now.first, now.second - 1) = regionNum;
					}
					if (WorkImage.at<uchar>(now.first - 1, now.second) == 255 && regionMap.at<int>(now.first - 1, now.second) == 0) {
						index.push(make_pair(now.first - 1, now.second));
						regionMap.at<int>(now.first - 1, now.second) = regionNum;
					}
				}
			}

    vector<pii> centers;
	vector<double> angles;
	Draw(regionMap, regionNum, Image, centers, angles);
	for (int i = 0; i < centers.size(); i++)
		cout << "centroid_x: " << centers[i].first << ", " << "centroid_y: " << centers[i].second << ", " << "principle_angle: " << angles[i] * 180 / CV_PI << endl;

    imshow(filename, Image);
    waitKey();

    return 0;
}