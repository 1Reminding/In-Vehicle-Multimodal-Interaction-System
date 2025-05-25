import cv2
import threading
import time


class CameraManager:
    """
    公共摄像头管理器，用于统一管理摄像头资源
    支持多个模块共享同一个摄像头
    """
    
    def __init__(self, camera_id=0):
        self.camera_id = camera_id
        self.cap = None
        self.is_opened = False
        self.lock = threading.Lock()
        self._initialize_camera()
    
    def _initialize_camera(self):
        """初始化摄像头"""
        try:
            self.cap = cv2.VideoCapture(self.camera_id)
            if not self.cap.isOpened():
                self.cap.release()
                self.cap = cv2.VideoCapture(self.camera_id)
                if not self.cap.isOpened():
                    raise RuntimeError(f"摄像头 {self.camera_id} 无法打开")
            
            self.is_opened = True
            print(f"摄像头 {self.camera_id} 初始化成功")
            
        except Exception as e:
            self.is_opened = False
            raise RuntimeError(f"摄像头初始化失败: {e}")
    
    def read_frame(self):
        """
        读取摄像头帧
        
        Returns:
            tuple: (success, frame) - success为布尔值，frame为图像帧
        """
        if not self.is_opened or self.cap is None:
            return False, None
            
        with self.lock:
            ret, frame = self.cap.read()
            return ret, frame
    
    def get_property(self, prop):
        """
        获取摄像头属性
        
        Args:
            prop: cv2.CAP_PROP_* 常量
            
        Returns:
            属性值
        """
        if not self.is_opened or self.cap is None:
            return None
            
        with self.lock:
            return self.cap.get(prop)
    
    def set_property(self, prop, value):
        """
        设置摄像头属性
        
        Args:
            prop: cv2.CAP_PROP_* 常量
            value: 要设置的值
            
        Returns:
            bool: 设置是否成功
        """
        if not self.is_opened or self.cap is None:
            return False
            
        with self.lock:
            return self.cap.set(prop, value)
    
    @property
    def width(self):
        """获取摄像头宽度"""
        return int(self.get_property(cv2.CAP_PROP_FRAME_WIDTH) or 0)
    
    @property
    def height(self):
        """获取摄像头高度"""
        return int(self.get_property(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
    
    def release(self):
        """释放摄像头资源"""
        with self.lock:
            if self.cap is not None:
                self.cap.release()
                self.cap = None
            self.is_opened = False
    
    def __del__(self):
        """析构函数，确保资源被释放"""
        self.release()


# 全局摄像头管理器实例
_camera_manager = None


def get_camera_manager(camera_id=0):
    """
    获取全局摄像头管理器实例（单例模式）
    
    Args:
        camera_id: 摄像头ID，默认为0
        
    Returns:
        CameraManager: 摄像头管理器实例
    """
    global _camera_manager
    if _camera_manager is None:
        _camera_manager = CameraManager(camera_id)
    return _camera_manager


def release_camera_manager():
    """释放全局摄像头管理器"""
    global _camera_manager
    if _camera_manager is not None:
        _camera_manager.release()
        _camera_manager = None 