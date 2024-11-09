from src.utils.commonImports import *
from src.models import model
from src.schemas import schemas
from src import crud

async def create_device_entry(
    db: AsyncSession,
    device: schemas.DeviceCreate, 
    owner_id: UUID
    ):
    # Check if a device with the same name already exists for the owner
    result = await db.execute(
        select(model.Device)
        .where(model.Device.device_name == device.device_name, model.Device.owner_id == owner_id))
    existing_device = result.scalar_one_or_none()
    
    if existing_device:
        raise HTTPException(status_code=400, detail="Device with this name already exists for the owner.")
    
    new_device = model.Device(
        device_id=uuid4(),
        device_name=device.device_name,
        owner_id=owner_id,
        device_model=device.device_model,
        location=device.location
    )
    
    # Add the new device to the session and commit
    db.add(new_device)
    await db.commit()
    await db.refresh(new_device)

    return new_device

# 1. Retrieve all devices created by a user
async def get_user_devices(
    db: AsyncSession,
    user_id: UUID
    ) -> List[model.Device]:
    result = await db.execute(select(model.Device)
                    .where(model.Device.owner_id == user_id)
                    .options(selectinload(model.Device.sensor_data)))
    devices = result.scalars().all()
    return devices

# 2. Update device information
async def update_device(
    db: AsyncSession,
    device_update: schemas.DeviceUpdate,
    device_id: UUID,
    user_id: UUID
    ) -> model.Device:
    result = await db.execute(select(model.Device)
                    .where(model.Device.device_id == device_id, model.Device.owner_id == user_id))
    device = result.scalar_one_or_none()

    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    for key, value in device_update.dict(exclude_unset=True).items():
        setattr(device, key, value)

    await db.commit()
    await db.refresh(device)
    return device

# 3. Delete a device
async def delete_device(
    db: AsyncSession,
    device_id: UUID, 
    user_id: UUID
    ):
    result = await db.execute(select(model.Device)
                     .where(model.Device.device_id == device_id, model.Device.owner_id == user_id))
    device = result.scalar_one_or_none()

    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    await db.delete(device)
    await db.commit()

# 4. Retrieve a device by its device_id
async def get_device_by_id(
    db: AsyncSession,
    device_id: UUID, 
    user_id: UUID) -> model.Device:
    result = await db.execute(
        select(model.Device)
        .where(model.Device.device_id == device_id, model.Device.owner_id == user_id)
        .options(selectinload(model.Device.sensor_data))
    )
    device = result.scalar_one_or_none()

    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    return device