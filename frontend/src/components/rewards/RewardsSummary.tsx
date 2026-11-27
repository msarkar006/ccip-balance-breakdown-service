import { Tile, Tag, Stack } from '@carbon/react';
import { formatDateTime } from '../../lib/utils';
import type { RewardsProgramme } from '../../types/rewards';
import styles from './RewardsSummary.module.scss';

interface RewardsSummaryProps {
  programme: RewardsProgramme | null;
}

export function RewardsSummary({ programme }: RewardsSummaryProps) {
  if (!programme) {
    return null;
  }

  return (
    <Tile className={styles.tile}>
      <Stack gap={5}>
        <div>
          <div className={styles.label}>Programme</div>
          <h3 className={styles.programmeName}>{programme.programme_name}</h3>
        </div>
        
        <div>
          <div className={styles.label}>Points balance</div>
          <div className={styles.points}>{programme.points_balance.toLocaleString()} points</div>
        </div>
        
        <div className={styles.status}>
          <Tag type="green" size="sm">{programme.status}</Tag>
          <span className={styles.asOf}>Points as of {formatDateTime(programme.as_of)}</span>
        </div>
      </Stack>
    </Tile>
  );
}
