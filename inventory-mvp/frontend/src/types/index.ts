export type OrderStatus = 'draft'|'created'|'checking_stock'|'waiting_items'|'ready_to_release'|'released'|'issued_to_workshop'|'received_by_workshop'|'in_progress'|'completed'|'cancelled'
export type InventoryStatus = 'available'|'reserved'|'issued'|'in_repair'|'written_off'|'lost'|'needs_check'

export interface InventoryItem { id:number; name:string; inventory_number?:string; status:InventoryStatus; available_quantity:number; reserved_quantity:number; issued_quantity:number; type:string }
export interface ProductionOrder { id:number; order_number:string; title:string; status:OrderStatus; priority:string }
