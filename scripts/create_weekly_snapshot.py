
import sys
import os
import structlog
import pandas as pd

# Add project root
sys.path.append(os.getcwd())

from core.portfolio.manager import SnapshotManager

logger = structlog.get_logger()

def main():
    print("📸 Iniciando Criação de Snapshot Semanal...")
    
    manager = SnapshotManager()
    
    # Optional: pass date as arg
    date_arg = None
    if len(sys.argv) > 1:
        date_arg = sys.argv[1]
        
    success = manager.create_snapshot(date_arg)
    
    if success:
        print("✅ Snapshot criado com sucesso! Carteira congelada.")
        
        # Verify
        latest = manager.get_latest_snapshot()
        if latest:
            print(f"📅 Data do Snapshot: {latest.get('snapshot_date')}")
            stats = latest.get('metadata', {})
            print(f"📊 Ativos congelados: {stats.get('total_assets')}")
    else:
        print("❌ Falha ao criar snapshot. Verifique os logs.")
        sys.exit(1)

if __name__ == "__main__":
    main()
