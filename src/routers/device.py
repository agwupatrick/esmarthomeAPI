from src.utils.commonImports import *
from src.utils.commonSession import get_session
from src.crud.users import get_current_active_user
from src.schemas import schemas
from src.models import model
from src import crud

router = APIRouter(prefix="/device", tags=["Device"])

@router.post("/devices/", response_model=schemas.DeviceOut, status_code=201)
async def create_device(
    device: schemas.DeviceCreate,
    db: AsyncSession = Depends(get_session),
    current_user: schemas.UserOut = Depends(get_current_active_user)
):
    return await crud.device.create_device_entry(db,device,current_user.user_id)

@router.get("/get-devices", response_model=List[schemas.DeviceOut])
async def retrieve_devices(
    db: AsyncSession = Depends(get_session),
    current_user: schemas.UserOut = Depends(get_current_active_user)
    ):
    devices = await crud.device.get_user_devices( db,current_user.user_id)
    return devices

@router.put("/{device_id}/update-device", response_model=schemas.DeviceOut)
async def update_device_info(
    device_update: schemas.DeviceUpdate,
    device_id: UUID,
    db: AsyncSession = Depends(get_session),
    current_user: schemas.UserOut = Depends(get_current_active_user)
):
    updated_device = await crud.device.update_device(db,device_update,device_id,current_user.user_id)
    return updated_device

@router.delete("/{device_id}/delete-device", status_code=204)
async def delete_device_endpoint(
    device_id: UUID,
    db: AsyncSession = Depends(get_session),
    current_user: schemas.UserOut = Depends(get_current_active_user)
):
    await crud.device.delete_device(db,device_id, current_user.user_id)
    return

@router.get("/{device_id}/get-device-by-id", response_model=schemas.DeviceWithSensorData)
async def retrieve_device_by_id(
    device_id: UUID,
    db: AsyncSession = Depends(get_session),
    current_user: schemas.UserOut = Depends(get_current_active_user)
):
    device = await crud.device.get_device_by_id(db,device_id, current_user.user_id)
    return device
