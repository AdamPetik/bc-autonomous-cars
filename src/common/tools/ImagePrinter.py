from matplotlib import pyplot as plt
import os


class ImagePrinter:
    def __init__(self):
        if not os.path.exists("images/heatmaps/"):
            os.makedirs("images/heatmaps/")

    def show2DArray(self, array):
        plt.imshow(array, interpolation='none')
        plt.show()

    def save2DArrayAsPicture(self, filename, array):
        plt.imshow(array, interpolation='none')
        plt.savefig("images/heatmaps/" + filename + '.png')
        # print(array)
