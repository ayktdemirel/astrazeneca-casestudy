import { Component, OnInit, NgZone, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { MatCardModule } from '@angular/material/card';
import { MatListModule } from '@angular/material/list';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { NotificationService, NotificationHistory } from '../../core/services/notification.service';

@Component({
  selector: 'app-notifications',
  standalone: true,
  imports: [
    CommonModule,
    MatCardModule,
    MatListModule,
    MatIconModule,
    MatButtonModule
  ],
  templateUrl: './notifications.html',
  styleUrl: './notifications.scss'
})
export class NotificationsComponent implements OnInit {
  notifications: NotificationHistory[] = [];
  loading = true;

  constructor(
    private notificationService: NotificationService,
    private router: Router,
    private zone: NgZone,
    private cdr: ChangeDetectorRef
  ) { }

  ngOnInit() {
    this.notificationService.getMyNotifications().subscribe({
      next: (data) => {
        this.zone.run(() => {
          this.notifications = data;
          this.loading = false;
          this.cdr.detectChanges();
        });
      },
      error: () => {
        this.zone.run(() => {
          this.notifications = [
            { id: '1', userId: 'u1', insightId: 'insight-demo1', channel: 'email', message: 'New Insight: Competitor X Phase 3', status: 'sent', sentAt: new Date().toISOString(), read: false },
            { id: '2', userId: 'u1', insightId: 'insight-demo2', channel: 'email', message: 'Insight: FDA Approval for Y', status: 'sent', sentAt: new Date(Date.now() - 3600000).toISOString(), read: true }
          ];
          this.loading = false;
          this.cdr.detectChanges();
        });
      }
    });
  }

  openInsight(notification: NotificationHistory) {
    const insightId = notification.insightId || notification.payload?.insight_id;
    if (insightId) {
      this.router.navigate(['/insights'], { queryParams: { id: insightId } });
    }
  }
}
