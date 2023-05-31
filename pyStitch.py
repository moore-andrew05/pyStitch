import numpy as np
import cv2

class Tile:
    def __init__(self, image_paths, log_path, x, y, stacks, microns_per_pixel, z_step):
        self.image_paths = image_paths
        self.channels = np.asarray([self._load_image(image) for image in image_paths])
        self.imshape = self.channels[0][0,:,:].shape
        self.micoords = x, y
        self.PIXELS_PER_MICRON = 1 / microns_per_pixel
        self.pxcoords = x*self.PIXELS_PER_MICRON, y*self.PIXELS_PER_MICRON
        #self._adjust_y()
        self.n_stacks = stacks
        self.z_step = z_step
        

    def _load_image(self, image_path):
        return np.asarray(cv2.imreadmulti(image_path)[1])
    
    def _adjust_y(self):
        self.pxcoords = (self.pxcoords[0], self.pxcoords[1] - self.imshape[1])
        

def parse_file(path, filename):
    with open(path + filename, 'r') as f:
        ind = 0
        channels = []
        for line in f:
            line = line.strip()

            if ind > 0:
                a = line.split()
                x = float(a[1])
                y = float(a[2])
                channels.append(path + ' '.join(a[6:]))
                ind -= 1

            if line.startswith("Z Planes"):
                z = int(line.split()[2])
            if line.startswith("Microns Per Pixel:"):
                mpp = float(line.split()[3])
            if line.startswith("Z Step"):
                z_step = float(line.split()[4])
            if line.startswith("Channels"):
                n_channels=int(line.split()[1])
            if line.startswith("IFD"):
                ind = n_channels

        f.close()
    return Tile(channels, path+filename, x, y, z, mpp, z_step)    

class Image:
    def __init__(self, tiles):
        self.tiles = tiles
        self.tile_shape = (self.tiles[0].imshape[1], self.tiles[0].imshape[0])
        self.canvas_width, self.canvas_height = self._adjust_tile_coords()
        self.canvas = np.zeros((self.tiles[0].channels.shape[0], self.tiles[0].n_stacks, self.canvas_height, self.canvas_width), dtype="uint8")
        self.canvas_layout = np.zeros((self.tiles[0].channels.shape[0], self.tiles[0].n_stacks, self.canvas_height, self.canvas_width), dtype="float32")

    def stitchatron_9000(self):
        for tile in self.tiles:
            self.canvas[:, :, tile.pxcoords[1]:tile.pxcoords[1]+self.tile_shape[1], 
                        (self.canvas_width - tile.pxcoords[0] - self.tile_shape[0]):(self.canvas_width - tile.pxcoords[0])] += tile.channels
            self.canvas_layout[:, :, tile.pxcoords[1]:tile.pxcoords[1]+self.tile_shape[1], 
                        (self.canvas_width - tile.pxcoords[0] - self.tile_shape[0]):(self.canvas_width - tile.pxcoords[0])] += 1
        self.canvas_layout[self.canvas_layout == 0] = 1
        self.canvas = self.canvas // np.sqrt(self.canvas_layout)

    def _adjust_tile_coords(self):
        minx = np.min([tile.pxcoords[0] for tile in self.tiles])
        miny = np.min([tile.pxcoords[1] for tile in self.tiles])
        for tile in self.tiles:
            tile.pxcoords = (int(tile.pxcoords[0]-minx), int(tile.pxcoords[1]-miny))
        return np.max([tile.pxcoords[0] for tile in self.tiles]) + self.tile_shape[0], \
                np.max([tile.pxcoords[1] for tile in self.tiles]) + self.tile_shape[1]

        