import { Component, Inject, Optional } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatDialogModule, MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatButtonModule } from '@angular/material/button';
import { MatSlideToggleModule } from '@angular/material/slide-toggle';

export interface JobDialogData {
  mode: 'create' | 'edit';
  job: {
    id?: string;
    source: string;
    query: string;
    schedule: string;
    enabled: boolean;
  };
}

@Component({
  selector: 'app-add-job-dialog',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    MatDialogModule,
    MatFormFieldModule,
    MatInputModule,
    MatSelectModule,
    MatButtonModule,
    MatSlideToggleModule
  ],
  template: `
    <div class="p-4" style="min-width: 400px;">
      <h2 class="text-xl font-bold text-gray-800 mb-6">{{ isEdit ? 'Edit Crawl Job' : 'Add New Crawl Job' }}</h2>

      <div class="space-y-4">
        <mat-form-field appearance="outline" class="w-full">
          <mat-label>Source</mat-label>
          <mat-select [(ngModel)]="job.source" required>
            <mat-option value="ClinicalTrials">ClinicalTrials.gov</mat-option>
            <mat-option value="ResearchNews">Research News (RSS)</mat-option>
          </mat-select>
        </mat-form-field>

        <mat-form-field appearance="outline" class="w-full">
          <mat-label>Search Query</mat-label>
          <input matInput [(ngModel)]="job.query" placeholder="e.g. Oncology, FDA, AstraZeneca" required>
          <mat-hint>Keywords to search for</mat-hint>
        </mat-form-field>

        <mat-form-field appearance="outline" class="w-full">
          <mat-label>Schedule (Cron)</mat-label>
          <mat-select [(ngModel)]="job.schedule">
            <mat-option value="* * * * *">Every minute</mat-option>
            <mat-option value="0 * * * *">Every hour</mat-option>
            <mat-option value="0 */4 * * *">Every 4 hours</mat-option>
            <mat-option value="0 */12 * * *">Every 12 hours</mat-option>
            <mat-option value="0 0 * * *">Daily</mat-option>
          </mat-select>
        </mat-form-field>

        <mat-slide-toggle [(ngModel)]="job.enabled" color="primary">
          Enable job immediately
        </mat-slide-toggle>
      </div>

      <div class="flex justify-end gap-2 mt-6">
        <button mat-button (click)="cancel()">Cancel</button>
        <button mat-raised-button color="primary"
          [disabled]="!job.source || !job.query"
          (click)="submit()">
          {{ isEdit ? 'Save Changes' : 'Create Job' }}
        </button>
      </div>
    </div>
  `
})
export class AddJobDialogComponent {
  isEdit = false;
  job: {
    id?: string;
    source: string;
    query: string;
    schedule: string;
    enabled: boolean;
  } = {
      source: '',
      query: '',
      schedule: '0 0 * * *',
      enabled: true
    };

  constructor(
    private dialogRef: MatDialogRef<AddJobDialogComponent>,
    @Optional() @Inject(MAT_DIALOG_DATA) public data: JobDialogData
  ) {
    if (data && data.mode === 'edit') {
      this.isEdit = true;
      this.job = { ...data.job };
    }
  }

  cancel() {
    this.dialogRef.close();
  }

  submit() {
    this.dialogRef.close({ ...this.job, mode: this.isEdit ? 'edit' : 'create' });
  }
}
