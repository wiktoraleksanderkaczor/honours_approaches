import numpy as np
from scipy.interpolate import interp2d

def undist_function(img_h, img_w, f_dist, xi, distorted_img, channels=3):
    u0_undist = img_w / 2  
    v0_undist = img_h / 2

    grid_x, grid_y = np.meshgrid(img_w, img_h)
    divider_u = f_dist - (u0_undist / f_dist)
    divider_v = f_dist - (v0_undist / f_dist)
    X_Cam = np.divide(grid_x, divider_u)
    Y_Cam  = np.divide(grid_y, divider_v)
    Z_Cam = np.ones((img_h, img_w))

    # Image to sphere cart
    xi1 = 0
    x = (1-xi1**2)
    X_Cam_pow2 = np.power(X_Cam, 2)
    Y_Cam_pow2 = np.power(Y_Cam, 2)
    Z_Cam_pow2 = np.power(Z_Cam, 2)
    alpha_cam = np.divide(
        np.multiply(xi1, \
            np.add(Z_Cam, \
                np.sqrt(
                    np.add(Z_Cam_pow2, \
                        np.multiply(x, \
                            np.add(
                                X_Cam_pow2, \
                                Y_Cam_pow2
                            )))))
        ),
        np.add(
            np.add(
                X_Cam_pow2, \
                Y_Cam_pow2
            ), \
                Z_Cam_pow2)
        )

    X_Sph = np.multiply(X_Cam, alpha_cam)
    Y_Sph = np.multiply(Y_Cam, alpha_cam)
    Z_Sph = np.subtract(np.multiply(Z_Cam, alpha_cam), xi1)
    X_Sph_pow2 = np.power(X_Sph, 2)
    Y_Sph_pow2 = np.power(Y_Sph, 2)
    Z_Sph_pow2 = np.power(Z_Sph, 2)

    # Reprojection on distorted
    added = np.add(X_Sph_pow2, np.add(Y_Cam_pow2, Z_Sph_pow2))
    ad_sqrt = np.sqrt(added)
    print(ad_sqrt)
    den = np.matmul(ad_sqrt, xi)
    den = np.add(den, Z_Sph)
    X_d = np.add(np.divide(np.matmul(X_Sph, f_dist), den), u0_undist)
    Y_d = np.add(np.divide(np.matmul(Y_Sph, f_dist), den), v0_undist)

    #Final step interpolation and mapping

    img_arr = np.zeros((img_h, img_w, channels))
    for channel in range(0, channels):
        img = distorted_img[:][:][channel]
        im2double = cv2.normalize(img.astype('float'), None, 0.0, 1.0, cv2.NORM_MINMAX)

        img_arr[:][:][channel] = interp2d(im2double, X_d, Y_d, kind="cubic")

    return img_arr