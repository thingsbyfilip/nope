from math import sqrt, tan, sin, cos, pi, ceil, floor, acos, atan, asin, degrees, radians, log, atan2, acos, asin


def getDistance(x1, y1, x2, y2):
	return sqrt( (x2 - x1)**2 + (y2 - y1)**2 )

def getAngle(x1, y1, x2, y2):
	return degrees(atan2(y2-y1, x2-x1))

def getPositionAtAngle(x1, y1, line_length, angle):
	return (x1 + line_length*cos(radians(angle)),y1 + line_length*sin(radians(angle)))

def getAngleDistance(angle1, angle2):
    diff = abs(angle1 % 360 - (angle2 % 360))
    if diff > 180:
        diff = 360 - diff
    return diff

#line functions
#adopted from https://www.redblobgames.com/grids/line-drawing/

def lerp(start, end, t):
	return start * (1.0 - t) + end * t;

def lerp_point(p0, p1, t):
	return (lerp(p0[0], p1[0], t), lerp(p0[1], p1[1], t))

def castRay(p0, p1,):
	points = []
	N = getDistance(p0[0], p0[1], p1[0], p1[1])

	for step in range(0, int(N+1)):
		t = 0 if N == 0 else step / N
		point = lerp_point(p0, p1, t)
		points.append( (int(round(point[0])), int(round(point[1]))) )

	return points