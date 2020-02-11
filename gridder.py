import numpy as np
import scipy.spatial as ss
from skimage import draw as skdraw


class Gridder(object):
    def __init__(self, tx, ty):
        self.tree = self.make_tree(tx, ty)

    def make_tree(self, tx, ty, dx=np.inf, center=False):
        """
        The method to create the lookup tree.
        
        Arguments
            tx [2-D array] -- The x coordinates of the grid
            ty [2-D array] -- The y coordinates of the grid
            dx [float] -- The delta between grid cells. Defaults to
                          infinity. This is used to provide slight 
                          speedup be limiting the spatial lookup extent.
                          If you are unsure; do not set this.
            center [bool] -- Boolean to determine whether the
                             lon/lat pair represents the center
                             or lower-left corner of the grid cell.
                             If not center, shift lon/lats to center.
                             Default is False.
                             
        Returns
            KDTree object    
        """
        tx = np.array(tx, copy=True, subok=True)
        ty = np.array(ty, copy=True, subok=True)
        if not center:
            x2 = tx.copy()
            y2 = ty.copy()
            x2[:, :-1] = tx[:, :-1] + (tx[:, 1:] - tx[:, :-1]) / 2.
            y2[:-1, :] = ty[:-1, :] + (ty[1:, :] - ty[:-1, :]) / 2.
            #np.add(x2[:, -1], (tx[:, -1] - tx[:, -2]) / 2., out=x2[:, -1], casting="unsafe")
            #np.add(y2[:, -1], (ty[:, -1] - ty[:, -2]) / 2., out=y2[:, -1], casting="unsafe")
            x2[:, -1] = x2[:, -1] + ((tx[:, -1] - tx[:, -2]) / 2.)
            y2[:, -1] = y2[:, -1] + ((ty[:, -1] - ty[:, -2]) / 2.)
            #x2[:, -1] += (tx[:, -1] - tx[:, -2]) / 2.
            #y2[-1, :] += (ty[-1, :] - ty[-2, :]) / 2.
            tx = x2.copy()
            ty = y2.copy()
            del(x2)
            del(y2)
        self.tx = tx; self.ty = ty; self.dx = dx
        self.tpoints = list(zip(tx.ravel(), ty.ravel()))
        return ss.cKDTree(self.tpoints)

    def _kdtree_query(self, x, y, dx):
        """
        Internal method to do spatial lookup.
        """
        try:
            points = np.asarray(list(zip(x, y)))
        except TypeError:
            points = np.asarray(list(zip([x], [y])))
        dists, inds = self.tree.query(points, k=1, distance_upper_bound=dx)
        bad_inds = np.where(inds >= len(self.tpoints))[0]
        inds = np.delete(inds, bad_inds)
        return np.unravel_index(inds, self.tx.shape)
    
    def grid_points(self, xs, ys):
        """
        Method to grid points.
        
        Arguments
            xs [list/array]: The x-coordinates
            yx [list/array]: The y-coordinates
            
        Returns
            A list of indices representing the points in grid space
        """
        xinds, yinds = self._kdtree_query(xs, ys, self.dx)
        points = list(zip(xinds, yinds))
        return points

    def grid_lines(self, sxs, sys, exs, eys):
        """
        Method to grid line segments.
        
        Arguments
            sxs [list/array]: The starting x-coordinates
            sys [list/array]: The starting y-coordinates
            exs [list/array]: The ending x-coordinates
            eys [list/array]: The ending y-coordinates
        
        Returns
            A list of indicides representing the lines in grid space.

        """
        sxinds, syinds = self._kdtree_query(sxs, sys, self.dx)
        exinds, eyinds = self._kdtree_query(exs, eys, self.dx)
        lines = [skdraw.line(sx, sy, ex, ey) for sx, sy, ex, ey in zip(sxinds, syinds, exinds, eyinds)]
        return lines
    
    def grid_polys(self, xs, ys):
        """
        Method to grid/fill polygons. Note: To just grid the boundary,
        use the "grid_lines" method.
        
        Arguments
            xs [list/array]: A list/array of lists/arrays of the x-coordinates 
                             of the polygons to grid.
            ys [list/array]: A list/array of lists/arrays of the y-coordinates 
                             of the polygons to grid.
                             
        Returns
            A list of arrays of indices representing the filled polygons
            in grid space
        """
        xinds, yinds = self._kdtree_query(xs, ys, self.dx)
        polys = [skdraw.polygon(x, y) for x, y in zip(xinds, yinds)]
        return polys
        