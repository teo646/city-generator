import pdb
import random

class city:
    class building:


        def getRegion(self, points):
            points = np.array(points)
            return [[np.min(points[:,0]),np.min(points[:,1])],[np.max(points[:,0]),np.max(points[:,1])]]

        def __init__(self, building_data):
            self.pos  = building_data['pos']
            self.y = building_data['y']
            self.x  = building_data['x']
            self.z = 300
            self.max_height  = building_data['max_height']
            self.R_edge  = building_data['R_edge']
            self.L_edge  = building_data['L_edge']
            self.U_edge  = building_data['U_edge']


        def drawBuilding(self, image, drawing, mask):
            try:
                region = self.getRegion([self.R_edge(self.x, self.L_edge(self.y, self.pos)),self.pos, self.L_edge(self.y, self.pos), self.R_edge(self.x, self.pos)])
                color = np.mean(image[region[0][1]:region[1][1],region[0][0]:region[1][0]])
            except Warning:
                color = 0
            self.z = self.max_height -  int(color/255*self.max_height)#(0~ max_height)

            building = np.zeros(image.shape, dtype='uint8')

            #draw columns
            building = cv2.line(building, self.pos, self.U_edge(self.z, self.pos), 255, line_thickness)
            building = cv2.line(building, self.R_edge(self.x, self.pos), self.U_edge(self.z, self.R_edge(self.x, self.pos)), 255, line_thickness)
            building = cv2.line(building, self.L_edge(self.y, self.pos), self.U_edge(self.z, self.L_edge(self.y, self.pos)), 255, line_thickness)


            #get num_floors and floor_height    
            last_point = self.R_edge(self.x, self.L_edge(self.y, self.U_edge(self.z, self.pos)))
            region = self.getRegion([last_point,self.pos, self.L_edge(self.y,self.pos), self.R_edge(self.x, self.pos)])
            area = (region[1][0]-region[0][0])*(region[1][1]-region[0][1])
            num_floors = int((255*area-np.sum(image[region[0][1]:region[1][1],region[0][0]:region[1][0]]))/(255*(self.x + self.y)*line_thickness)/2.5)-2
            if num_floors <= 0:
                return drawing, mask
            floor_height = self.z/num_floors
            if floor_height < 5:
                floor_height = 5
                num_floors = int(self.z/5)
            #draw sides
            for floor in range(num_floors+1):
                pos = self.U_edge(int(floor*floor_height), self.pos)
                building = cv2.line(building, pos, self.R_edge(self.x, pos), 255, line_thickness )
                building = cv2.line(building, pos, self.L_edge(self.y, pos), 255, line_thickness )

            #draw top
            building = cv2.line(building, self.R_edge(self.x, self.U_edge(self.z, self.pos)), last_point, 255, line_thickness )
            building = cv2.line(building, self.L_edge(self.y, self.U_edge(self.z, self.pos)), last_point, 255, line_thickness )

            #draw the building on the drawing
            drawing[region[0][1]:region[1][1],region[0][0]:region[1][0]+3]=  np.add(np.multiply(building[region[0][1]:region[1][1],region[0][0]:region[1][0]+3], mask[region[0][1]:region[1][1],region[0][0]:region[1][0]+3]), drawing[region[0][1]:region[1][1],region[0][0]:region[1][0]+3])

            #masking
            points = np.array([self.pos, self.R_edge(self.x, self.pos), self.R_edge(self.x, self.U_edge(self.z, self.pos)), last_point, self.L_edge(self.y, self.U_edge(self.z, self.pos)), self.L_edge(self.y, self.pos)])
            mask = cv2.fillPoly(mask, [points], 0)
            return drawing, mask

    def OrderingBuildings(self,building_map):
        building_map = sorted(building_map, key=lambda building: building[0][1],reverse=True)
        return building_map

    def createBuildingMap(self, shape, building_range, building_num, R_edge, L_edge):
        building_map = []
        sites = np.zeros(shape, dtype='uint8')
        for i in range(building_num):
            pos = [random.randrange(0, shape[1]), random.randrange(0, shape[0])]
            x = random.randrange(building_range[0], building_range[1])
            y = random.randrange(building_range[0], building_range[1])

            points = np.array([pos, R_edge(x,pos), R_edge(x,L_edge(y,pos)), L_edge(y,pos)])
            if(np.all(sites[points[2][1] if points[2][1]>0 else 0:points[0][1],points[3][0] if points[3][0]>0 else 0:points[1][0]] == 0)):
                sites = cv2.fillPoly(sites,[points],1)
                building_map.append([pos,x,y])
        return self.OrderingBuildings(building_map)


    def __init__(self, image, yaw, pitch, building_range, building_num, max_height):
        self.image = resize_image(image, 25000000)
        brightness = np.mean(self.image)/255
        ratio = 0.4/brightness
        self.image = cv2.convertScaleAbs(self.image, alpha=ratio, beta=0)

        #this process mathmatically find visual length of edges of buildings based on actual length and view point 
        z_coeff = math.cos(pitch)
        x_coeff = math.sqrt(1-math.sin(yaw)**2*(1-math.sin(pitch)**2))
        y_coeff = math.sqrt(1-math.cos(yaw)**2*(1-math.sin(pitch)**2))
        TanX = math.tan(yaw)*math.sin(pitch)
        CosX = TanX/math.sqrt(TanX**2 + 1)
        SinX = 1/math.sqrt(TanX**2 + 1)
        TanY = math.sin(pitch)/math.tan(yaw)
        CosY = TanY/math.sqrt(TanY**2 + 1)
        SinY = 1/math.sqrt(TanY**2 + 1)
        def R_edge(x,pos):
             return [pos[0]+int(SinX*x_coeff*x),pos[1]-int(CosX*x_coeff*x)]

        def L_edge(y,pos):
             return [pos[0]-int(SinY*y_coeff*y),pos[1]-int(CosY*y_coeff*y)]

        def U_edge(z, pos):
             return [pos[0], pos[1]-int(z*z_coeff)]

        building_map = self.createBuildingMap(self.image.shape, building_range, building_num, R_edge, L_edge)
        self.buildings = []
        for building in building_map:
            x = building[1]
            y = building[2]

            building_data = {'pos':building[0], 'x': x, 'y':y, 'max_height':max_height, 'R_edge':R_edge, 'L_edge':L_edge, 'U_edge':U_edge}
            self.buildings.append(self.building(building_data))

    def drawBuildings(self):
        drawing = np.zeros(self.image.shape, dtype='uint8')
        mask = np.ones(self.image.shape, dtype="uint8")
        for building in self.buildings:
            drawing, mask = building.drawBuilding(self.image, drawing, mask)

        return 255-drawing

